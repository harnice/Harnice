"""
feature_tree_server.py
HTTP server for the harnice feature tree editor.
Serves the editor HTML and provides REST API for file I/O, project switching,
subprocess run, and native folder browsing.

Usage (from a rev folder):
    python -m harnice --feature-tree-editor
or directly:
    python feature_tree_server.py /path/to/rev/folder
"""

import http.server
import json
import os
import queue
import subprocess
import sys
import threading
import webbrowser
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_GUI_DIR = Path(__file__).resolve().parent
_FUNCTION_INDEX = _GUI_DIR / "function_index.json"
_EDITOR_HTML = _GUI_DIR / "feature_tree_editor.html"


def _gui_state_path() -> Path:
    """gui_state.json sits at the harnice project root (two levels above gui/)."""
    return _GUI_DIR.parents[1] / "gui_state.json"


# ---------------------------------------------------------------------------
# State — shared, protected by a lock
# ---------------------------------------------------------------------------

class _State:
    def __init__(self, rev_folder: str):
        self.lock = threading.Lock()
        self._rev_folder = ""
        self._feature_tree_path = None
        self.set_rev_folder(rev_folder)

        # Run subprocess state
        self.run_proc = None
        self.run_output = queue.Queue()   # lines as {"text": ..., "stream": "stdout"|"stderr"}
        self.run_done = False
        self.run_exit_code = None

    # ---- project ----

    def set_rev_folder(self, rev_folder: str):
        folder = os.path.normpath(os.path.abspath(rev_folder))
        with self.lock:
            self._rev_folder = folder
            self._feature_tree_path = self._resolve_feature_tree(folder)

    def _resolve_feature_tree(self, folder: str):
        try:
            from harnice import fileio
            old = os.getcwd()
            os.chdir(folder)
            try:
                p = fileio.path("feature tree")
            finally:
                os.chdir(old)
            return Path(p)
        except Exception as e:
            print(f"[server] could not resolve feature tree path: {e}", file=sys.stderr)
            return None

    @property
    def rev_folder(self) -> str:
        with self.lock:
            return self._rev_folder

    @property
    def feature_tree_path(self):
        with self.lock:
            return self._feature_tree_path

    # ---- pn / rev ----

    def pn_and_rev(self):
        folder = self.rev_folder
        rev_folder = os.path.normpath(folder)
        part_dir = os.path.dirname(rev_folder)
        rev_name = os.path.basename(rev_folder)
        part_name = os.path.basename(part_dir)
        if not rev_name.startswith(f"{part_name}-rev"):
            return "", ""
        rev_str = rev_name.split("-rev")[-1]
        if not rev_str.isdigit():
            return "", ""
        return part_name, f"rev{rev_str}"

    # ---- code file ----

    def read_code(self) -> str:
        p = self.feature_tree_path
        if p is None or not p.exists():
            return ""
        return p.read_text(encoding="utf-8")

    def write_code(self, code: str):
        p = self.feature_tree_path
        if p is None:
            raise RuntimeError("No feature tree path resolved.")
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(code, encoding="utf-8")


_state: _State = None  # initialised in run_server()


# ---------------------------------------------------------------------------
# gui_state.json — remembered projects
# ---------------------------------------------------------------------------

def _load_gui_state() -> dict:
    p = _gui_state_path()
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"recent_projects": []}


def _save_gui_state(data: dict):
    p = _gui_state_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _add_recent_project(rev_folder: str):
    data = _load_gui_state()
    projects = data.get("recent_projects", [])
    # Normalise and deduplicate, most recent first
    norm = os.path.normpath(os.path.abspath(rev_folder))
    projects = [p for p in projects if os.path.normpath(p) != norm]
    projects.insert(0, norm)
    data["recent_projects"] = projects[:50]  # cap at 50
    _save_gui_state(data)


def _remove_recent_project(rev_folder: str):
    data = _load_gui_state()
    norm = os.path.normpath(os.path.abspath(rev_folder))
    data["recent_projects"] = [
        p for p in data.get("recent_projects", [])
        if os.path.normpath(p) != norm
    ]
    _save_gui_state(data)


# ---------------------------------------------------------------------------
# Run subprocess
# ---------------------------------------------------------------------------

def _stream_output(proc, state: _State):
    """Read stdout and stderr from proc into state.run_output queue."""
    def _read(stream, label):
        for line in iter(stream.readline, ""):
            state.run_output.put({"text": line.rstrip("\n"), "stream": label})
        stream.close()

    t_out = threading.Thread(target=_read, args=(proc.stdout, "stdout"), daemon=True)
    t_err = threading.Thread(target=_read, args=(proc.stderr, "stderr"), daemon=True)
    t_out.start()
    t_err.start()
    t_out.join()
    t_err.join()
    proc.wait()

    with state.lock:
        state.run_exit_code = proc.returncode
        state.run_done = True


def _start_run(state: _State):
    with state.lock:
        if state.run_proc and state.run_proc.poll() is None:
            return  # already running
        # Reset output state
        state.run_output = queue.Queue()
        state.run_done = False
        state.run_exit_code = None

    try:
        proc = subprocess.Popen(
            [sys.executable, "-m", "harnice", "-r"],
            cwd=state.rev_folder,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
    except OSError as e:
        state.run_output.put({"text": f"[error] could not start harnice: {e}", "stream": "stderr"})
        with state.lock:
            state.run_done = True
            state.run_exit_code = -1
        return

    with state.lock:
        state.run_proc = proc

    threading.Thread(target=_stream_output, args=(proc, state), daemon=True).start()


# ---------------------------------------------------------------------------
# HTTP handler
# ---------------------------------------------------------------------------

class FeatureTreeHandler(http.server.BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        pass  # suppress access log

    # ---- routing ----

    def do_GET(self):
        routes = {
            "/":                    self._serve_html,
            "/index.html":          self._serve_html,
            "/api/info":            self._api_info,
            "/api/code":            self._api_get_code,
            "/api/function_index":  self._api_function_index,
            "/api/run_output":      self._api_run_output,
            "/api/recent_projects": self._api_recent_projects,
            "/api/browse":          self._api_browse,
        }
        handler = routes.get(self.path)
        if handler:
            handler()
        else:
            self.send_error(404)

    def do_POST(self):
        routes = {
            "/api/code":              self._api_post_code,
            "/api/run":               self._api_run,
            "/api/switch":            self._api_switch,
            "/api/remove_project":    self._api_remove_project,
            "/api/close":             self._api_close,
        }
        handler = routes.get(self.path)
        if handler:
            handler()
        else:
            self.send_error(404)

    # ---- GET handlers ----

    def _serve_html(self):
        if not _EDITOR_HTML.exists():
            self.send_error(500, "feature_tree_editor.html not found")
            return
        self._send_bytes(_EDITOR_HTML.read_bytes(), "text/html; charset=utf-8")

    def _api_info(self):
        pn, rev = _state.pn_and_rev()
        p = _state.feature_tree_path
        self._send_json({
            "part_number": pn,
            "rev": rev,
            "feature_tree_path": str(p) if p else None,
            "rev_folder": _state.rev_folder,
        })

    def _api_get_code(self):
        try:
            code = _state.read_code()
            self._send_json({"code": code})
        except Exception as e:
            self._send_json({"error": str(e)}, status=500)

    def _api_function_index(self):
        if not _FUNCTION_INDEX.exists():
            self._send_json({"error": "function_index.json not found — run build_gui.py"}, status=500)
            return
        self._send_bytes(_FUNCTION_INDEX.read_bytes(), "application/json; charset=utf-8")

    def _api_run_output(self):
        """Return all queued output lines since last poll, plus done/exit_code."""
        lines = []
        try:
            while True:
                lines.append(_state.run_output.get_nowait())
        except queue.Empty:
            pass
        with _state.lock:
            done = _state.run_done
            exit_code = _state.run_exit_code
        self._send_json({"lines": lines, "done": done, "exit_code": exit_code})

    def _api_recent_projects(self):
        data = _load_gui_state()
        self._send_json({"projects": data.get("recent_projects", [])})

    def _api_browse(self):
        path = None
        error = None
        try:
            import tkinter as tk
            from tkinter import filedialog
            root = tk.Tk()
            root.withdraw()
            root.attributes("-topmost", True)
            selected = filedialog.askdirectory(title="Select revision folder")
            root.destroy()
            path = selected if selected else None
        except Exception as e:
            error = str(e)
        self._send_json({"path": path, "error": error})

    # ---- POST handlers ----

    def _api_post_code(self):
        body = self._read_json_body()
        code = body.get("code", "")
        try:
            _state.write_code(code)
            self._send_json({"ok": True})
        except Exception as e:
            self._send_json({"ok": False, "error": str(e)}, status=500)

    def _api_run(self):
        _start_run(_state)
        self._send_json({"ok": True})

    def _api_switch(self):
        body = self._read_json_body()
        folder = body.get("rev_folder", "").strip()
        if not folder or not os.path.isdir(folder):
            self._send_json({"ok": False, "error": "invalid folder"}, status=400)
            return
        _state.set_rev_folder(folder)
        _add_recent_project(folder)
        pn, rev = _state.pn_and_rev()
        p = _state.feature_tree_path
        self._send_json({
            "ok": True,
            "part_number": pn,
            "rev": rev,
            "feature_tree_path": str(p) if p else None,
        })

    def _api_remove_project(self):
        body = self._read_json_body()
        folder = body.get("rev_folder", "").strip()
        if folder:
            _remove_recent_project(folder)
        self._send_json({"ok": True})

    def _api_close(self):
        self._send_json({"ok": True})
        threading.Thread(target=self.server.shutdown, daemon=True).start()

    # ---- helpers ----

    def _read_json_body(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def _send_json(self, data: dict, status: int = 200):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_bytes(self, data: bytes, content_type: str):
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def run_server(rev_folder: str = None, port: int = 0, open_browser: bool = True):
    global _state

    if rev_folder is None:
        rev_folder = os.getcwd()

    rev_folder = os.path.normpath(os.path.abspath(rev_folder))
    _state = _State(rev_folder)
    _add_recent_project(rev_folder)

    server = http.server.HTTPServer(("127.0.0.1", port), FeatureTreeHandler)
    actual_port = server.server_address[1]
    url = f"http://127.0.0.1:{actual_port}/"

    # Write URL to env-var file (same pattern as graph_server.py)
    url_file = os.environ.get("HARNICE_FEATURE_TREE_EDITOR_URL_FILE")
    if url_file:
        try:
            Path(url_file).write_text(url, encoding="utf-8")
        except Exception:
            pass

    print(f"Feature tree editor: {url}  (Ctrl+C to stop)")

    if open_browser:
        webbrowser.open(url)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[server] stopped.")


if __name__ == "__main__":
    folder = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    run_server(rev_folder=folder)