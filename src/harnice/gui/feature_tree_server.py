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

import csv
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


def _debug(msg: str):
    """Print to stderr so you see exactly what the server is doing when you click."""
    print(f"[ft-server] {msg}", file=sys.stderr, flush=True)


def _find_feature_tree_path_in_structure(structure, path=None):
    """Return list of path segments (keys) to the 'feature tree' value in the structure dict, or [] if not found. No chdir or fileio."""
    if path is None:
        path = []
    if isinstance(structure, dict):
        for key, value in structure.items():
            if value == "feature tree":
                return path + [key]
            result = _find_feature_tree_path_in_structure(value, path + [key])
            if result:
                return result
    elif isinstance(structure, list):
        for i, item in enumerate(structure):
            result = _find_feature_tree_path_in_structure(item, path + [f"[{i}]"])
            if result:
                return result
    return []


def _gui_state_path() -> Path:
    """
    Path to feature_tree_editor_state.json.

    Stored at the harnice project root alongside gui_layout.json (and separate
    from any launcher_state.json), which is three levels above this gui/
    directory.
    """
    return _GUI_DIR.parents[2] / "feature_tree_editor_state.json"


# ---------------------------------------------------------------------------
# State — shared, protected by a lock
# ---------------------------------------------------------------------------


class _State:
    def __init__(self, rev_folder: str):
        self.lock = threading.Lock()
        self._rev_folder = ""
        self._feature_tree_path = None
        self._feature_tree_error = None  # reason when path could not be resolved
        self.set_rev_folder(rev_folder)

        # Run subprocess state
        self.run_proc = None
        self.run_output = (
            queue.Queue()
        )  # lines as {"text": ..., "stream": "stdout"|"stderr"}
        self.run_done = False
        self.run_exit_code = None

    # ---- project ----

    def set_rev_folder(self, rev_folder: str):
        folder = os.path.normpath(os.path.abspath(rev_folder))
        _debug(f"set_rev_folder called with: {folder!r}")
        with self.lock:
            self._rev_folder = folder
            self._feature_tree_path, self._feature_tree_error = (
                self._resolve_feature_tree(folder)
            )
        _debug(
            f"after resolve: feature_tree_path={self._feature_tree_path!r} error={self._feature_tree_error!r}"
        )

    def _resolve_feature_tree(self, folder: str):
        """
        Resolve the feature tree file path from the rev folder path only.
        No chdir: we read revision history and product file_structure using
        the given path, then build the feature tree path as rev_folder + structure key.
        Returns (Path or None, error_message or None).
        """
        try:
            from harnice import state

            rev_folder = os.path.normpath(os.path.abspath(folder))
            part_dir = os.path.dirname(rev_folder)
            rev_name = os.path.basename(rev_folder)
            part_name = os.path.basename(part_dir)

            _debug(
                f"_resolve_feature_tree: rev_folder={rev_folder!r} part_dir={part_dir!r} part_name={part_name!r} rev_name={rev_name!r}"
            )

            if not rev_name.startswith(f"{part_name}-rev"):
                raise RuntimeError(f"Not a revision folder: {rev_folder}")
            suffix = rev_name.split("-rev", 1)[-1]
            if not suffix:
                raise RuntimeError(f"Not a revision folder: {rev_folder}")

            state.set_pn(part_name)
            state.set_rev(int(suffix) if suffix.isdigit() else suffix)
            _debug(f"  state.pn={state.pn!r} state.rev={state.rev!r}")

            rev_hist_path = os.path.join(part_dir, f"{part_name}-revision_history.tsv")
            _debug(
                f"  rev_hist_path={rev_hist_path!r} exists={os.path.exists(rev_hist_path)}"
            )
            if not os.path.exists(rev_hist_path):
                raise RuntimeError(f"Revision history not found: {rev_hist_path}")

            with open(rev_hist_path, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f, delimiter="\t")
                rows = list(reader)
            _debug(f"  revision_history rows: {len(rows)}")

            product_type = None
            rev_str = str(state.rev)
            for row in rows:
                raw = (row.get("rev") or "").strip()
                match = raw == rev_str
                if not match and raw.isdigit() and rev_str.isdigit():
                    try:
                        match = int(raw) == int(state.rev)
                    except (ValueError, TypeError):
                        pass
                if match:
                    product_type = (row.get("product") or "").strip()
                    break

            _debug(f"  product_type={product_type!r}")
            if not product_type:
                raise RuntimeError(f"No product type for revision folder: {rev_folder}")

            product_module = __import__(
                f"harnice.products.{product_type}", fromlist=[product_type]
            )
            if not hasattr(product_module, "file_structure"):
                raise RuntimeError(f"Product '{product_type}' has no file_structure()")

            structure = product_module.file_structure()
            path_parts = _find_feature_tree_path_in_structure(structure)
            _debug(f"  path_parts (feature tree key)={path_parts!r}")
            if not path_parts:
                raise RuntimeError(
                    f"Product '{product_type}' file_structure has no 'feature tree' entry"
                )

            full_path = os.path.join(rev_folder, *path_parts)
            _debug(f"  full_path={full_path!r} exists={os.path.exists(full_path)}")
            return Path(full_path), None
        except Exception as e:
            err = str(e)
            _debug(f"_resolve_feature_tree FAILED: {err}")
            return None, err

    @property
    def rev_folder(self) -> str:
        with self.lock:
            return self._rev_folder

    @property
    def feature_tree_path(self):
        with self.lock:
            return self._feature_tree_path

    # ---- pn / rev (use state.partnumber per docs: Keeping Track of Files) ----

    def pn_and_rev(self):
        try:
            from harnice import state

            return state.partnumber("pn"), state.partnumber("rev")
        except (NameError, ValueError):
            # Fallback if state not set or wrong format
            folder = self.rev_folder
            rev_folder = os.path.normpath(folder)
            part_dir = os.path.dirname(rev_folder)
            rev_name = os.path.basename(rev_folder)
            part_name = os.path.basename(part_dir)
            if not rev_name.startswith(f"{part_name}-rev"):
                return "", ""
            rev_str = rev_name.split("-rev", 1)[-1]
            return part_name, f"rev{rev_str}" if rev_str else ("", "")

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
# feature_tree_editor_state.json — remembered projects
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
        p for p in data.get("recent_projects", []) if os.path.normpath(p) != norm
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


def _stop_run(state: _State):
    """Stop the current run subprocess (harnice -r) if any."""
    with state.lock:
        proc = state.run_proc
        state.run_proc = None
    if proc is not None and proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()


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
        state.run_output.put(
            {"text": f"[error] could not start harnice: {e}", "stream": "stderr"}
        )
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
        path = self.path.split("?")[0]
        routes = {
            "/": self._serve_html,
            "/index.html": self._serve_html,
            "/api/info": self._api_info,
            "/api/code": self._api_get_code,
            "/api/function_index": self._api_function_index,
            "/api/run_output": self._api_run_output,
            "/api/recent_projects": self._api_recent_projects,
            "/api/browse": self._api_browse,
        }
        handler = routes.get(path)
        if handler:
            handler()
        else:
            self.send_error(404)

    def do_POST(self):
        path = self.path.split("?")[0]
        routes = {
            "/api/code": self._api_post_code,
            "/api/run": self._api_run,
            "/api/switch": self._api_switch,
            "/api/add_project": self._api_add_project,
            "/api/select_project": self._api_select_project,
            "/api/remove_project": self._api_remove_project,
            "/api/close": self._api_close,
        }
        handler = routes.get(path)
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
        self._send_json(
            {
                "part_number": pn,
                "rev": rev,
                "feature_tree_path": str(p) if p else None,
                "rev_folder": _state.rev_folder,
            }
        )

    def _api_get_code(self):
        _debug("GET /api/code")
        try:
            if _state.feature_tree_path is None:
                _debug(
                    "  -> feature_tree_path is None, returning feature_tree_resolved=False"
                )
                self._send_json(
                    {
                        "code": "",
                        "feature_tree_resolved": False,
                        "feature_tree_error": _state._feature_tree_error
                        or "feature tree not found",
                    }
                )
                return
            code = _state.read_code()
            _debug(f"  -> path={_state.feature_tree_path!r} code_len={len(code)}")
            self._send_json({"code": code, "feature_tree_resolved": True})
        except Exception as e:
            _debug(f"  -> ERROR: {e}")
            self._send_json({"error": str(e)}, status=500)

    def _api_function_index(self):
        if not _FUNCTION_INDEX.exists():
            self._send_json(
                {
                    "error": (
                        "function_index.json not found — run "
                        "build_feature_tree_gui.py to generate it"
                    )
                },
                status=500,
            )
            return
        self._send_bytes(
            _FUNCTION_INDEX.read_bytes(), "application/json; charset=utf-8"
        )

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
        _debug(
            f"POST /api/switch rev_folder={folder!r} isdir={os.path.isdir(folder) if folder else False}"
        )
        if not folder or not os.path.isdir(folder):
            _debug("  -> 400 invalid folder")
            self._send_json({"ok": False, "error": "invalid folder"}, status=400)
            return
        _state.set_rev_folder(folder)
        _add_recent_project(folder)
        pn, rev = _state.pn_and_rev()
        p = _state.feature_tree_path
        _debug(f"  -> ok part_number={pn!r} rev={rev!r} feature_tree_path={p!r}")
        self._send_json(
            {
                "ok": True,
                "part_number": pn,
                "rev": rev,
                "feature_tree_path": str(p) if p else None,
            }
        )

    def _api_add_project(self):
        """Add a rev folder to the recent-projects list only; do not switch or load."""
        body = self._read_json_body()
        folder = body.get("rev_folder", "").strip()
        _debug(f"POST /api/add_project rev_folder={folder!r}")
        if not folder or not os.path.isdir(folder):
            self._send_json({"ok": False, "error": "invalid folder"}, status=400)
            return
        _add_recent_project(folder)
        self._send_json({"ok": True})

    def _api_select_project(self):
        """Run fileio.verify_revision_structure() in a subprocess with cwd=rev_folder; kill any running harnice -r; return exit_code and output for the console. Client should then switch + load code if exit_code is 0."""
        body = self._read_json_body()
        folder = body.get("rev_folder", "").strip()
        _debug(f"POST /api/select_project rev_folder={folder!r}")
        if not folder or not os.path.isdir(folder):
            self._send_json({"ok": False, "error": "invalid folder"}, status=400)
            return
        folder = os.path.normpath(os.path.abspath(folder))

        _stop_run(_state)
        _debug("  running verify_revision_structure subprocess...")

        try:
            result = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    "from harnice import fileio; fileio.verify_revision_structure(); import sys; sys.exit(0)",
                ],
                cwd=folder,
                capture_output=True,
                text=True,
                timeout=60,
            )
            exit_code = result.returncode
            stdout = result.stdout or ""
            stderr = result.stderr or ""
        except subprocess.TimeoutExpired:
            exit_code = -1
            stdout = ""
            stderr = "verify_revision_structure timed out"
            _debug("  subprocess TIMEOUT")
        except Exception as e:
            exit_code = -1
            stdout = ""
            stderr = str(e)
            _debug(f"  subprocess EXCEPTION: {e}")

        _debug(f"  select_project done exit_code={exit_code}")

        self._send_json(
            {
                "ok": True,
                "exit_code": exit_code,
                "stdout": stdout,
                "stderr": stderr,
            }
        )

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
    _debug(f"run_server starting rev_folder={rev_folder!r}")
    _state = _State(rev_folder)
    _add_recent_project(rev_folder)
    _debug(
        f"initial feature_tree_path={_state.feature_tree_path!r} error={_state._feature_tree_error!r}"
    )

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
