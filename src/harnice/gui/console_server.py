"""
console_server.py
HTTP server for the Harnice console.
Serves the editor HTML and provides REST API for file I/O, project switching,
subprocess run, and native folder browsing.

Usage:
    python -m harnice --console
    harnice-gui
or with a revision folder:
    python -m harnice.gui.console_server /path/to/rev/folder
"""

import csv
import http.server
import json
import os
import queue
import socketserver
import subprocess
import sys
import threading
import webbrowser
from pathlib import Path

from harnice.gui import system_viewer_core, system_viewer_server

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_GUI_DIR = Path(__file__).resolve().parent
_FUNCTION_INDEX = _GUI_DIR / "function_index.json"
_EDITOR_HTML = _GUI_DIR / "harnice_console.html"
_GRAPH_EDITOR_HTML = _GUI_DIR / "graph_editor.html"
_SYSTEM_LIST_VIEW_JS = _GUI_DIR / "system_list_view.js"


def _graph_file_path(rev_folder: str, product_type: str, label: str) -> Path:
    """Return the absolute path for a graph-editor file label. No global state. Harness only."""
    if product_type != "harness":
        raise ValueError("Graph files only exist for harness product")
    rev_name = os.path.basename(os.path.normpath(rev_folder))
    # Harness file_structure keys: {pn-rev}-available_network.json, etc.
    key_by_label = {
        "available network": f"{rev_name}-available_network.json",
        "chosen network": f"{rev_name}-chosen_network.json",
        "flattened network": f"{rev_name}-flattened_network.tsv",
        "chosen entity list": f"{rev_name}-chosen_entity_list.json",
    }
    key = key_by_label.get(label)
    if not key:
        raise ValueError(f"Unknown graph file label: {label}")
    return Path(rev_folder) / key


def _graph_read_json(path: Path, default):
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default


def _graph_write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def _graph_read_csv(path: Path):
    if not path.exists():
        return [], []
    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return reader.fieldnames or [], list(reader)


def _graph_write_csv(path: Path, fieldnames, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _editor_files_for_product(product_type: str, rev_folder: str = None) -> list:
    """Return list of file labels to show in the file navigator for this product. Harness has network files; system has system list panes (dynamic from project)."""
    if product_type == "harness":
        return [
            "feature tree",
            "available network",
            "chosen network",
            "flattened network",
        ]
    if product_type == "system" and rev_folder:
        try:
            tabs = system_viewer_core.get_tab_list()
            return ["feature tree"] + [label for (_k, label) in tabs]
        except Exception:
            pass
    if product_type == "system":
        return ["feature tree", "system lists"]
    return ["feature tree"]


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
    Path to console state file (harnice_console_state.json).

    Stored at the harnice project root (three levels above this gui/ directory).
    """
    return _GUI_DIR.parents[2] / "harnice_console_state.json"


def _product_type_for_revision_folder(rev_folder: str):
    """
    Return the Harnice product type (e.g. "harness", "system") for a revision
    folder path, or None if it cannot be determined. Supports numeric and
    string rev suffixes (e.g. rev9, revA).
    """
    info = _project_info_for_revision_folder(rev_folder)
    return info.get("product_type") if info else None


def _button_color_for_product(product_type: str):
    """Return button_color from the product module for UI theming."""
    if not product_type:
        return None
    try:
        product_module = __import__(
            f"harnice.products.{product_type}", fromlist=[product_type]
        )
        return getattr(product_module, "button_color", None)
    except Exception:
        return None


def _project_info_for_revision_folder(rev_folder: str) -> dict:
    """
    Return dict with product_type, description, button_color for a revision folder,
    or None if not determinable. Uses revision_history.tsv row (product, desc) and
    product module button_color.
    """
    rev_folder = os.path.normpath(os.path.abspath(rev_folder))
    part_dir = os.path.dirname(rev_folder)
    rev_name = os.path.basename(rev_folder)
    part_name = os.path.basename(part_dir)
    if not rev_name.startswith(f"{part_name}-rev"):
        return None
    suffix = rev_name.split("-rev", 1)[-1]
    if not suffix:
        return None
    rev_hist_path = os.path.join(part_dir, f"{part_name}-revision_history.tsv")
    if not os.path.exists(rev_hist_path):
        return None
    try:
        from harnice.lists import rev_history

        row = rev_history.info(rev=suffix, path=rev_hist_path)
        if not row or not isinstance(row, dict):
            return None
        product_type = (row.get("product") or "").strip() or None
        description = (row.get("desc") or "").strip() or None
        button_color = _button_color_for_product(product_type) if product_type else None
        return {
            "product_type": product_type,
            "description": description,
            "button_color": button_color,
        }
    except Exception:
        return None


# ---------------------------------------------------------------------------
# State — shared, protected by a lock
# ---------------------------------------------------------------------------


class _State:
    def __init__(self, rev_folder: str):
        self.lock = threading.Lock()
        self._rev_folder = ""
        self._feature_tree_path = None
        self._feature_tree_error = None  # reason when path could not be resolved
        self._product_type = None
        self._editor_files = ["feature tree"]  # file labels for file navigator
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
        with self.lock:
            self._rev_folder = folder
            path, err, ptype = self._resolve_feature_tree(folder)
            self._feature_tree_path = path
            self._feature_tree_error = err
            self._product_type = ptype
            self._editor_files = (
                _editor_files_for_product(ptype, folder) if ptype else ["feature tree"]
            )
        # Switch process cwd to rev folder so fileio.rev_directory() (getcwd()) is correct;
        # system list panes and other fileio.path() lookups then resolve to this project.
        try:
            os.chdir(folder)
        except OSError:
            pass

    def _resolve_feature_tree(self, folder: str):
        """
        Resolve the feature tree file path from the rev folder path only.
        No chdir: we read revision history and product file_structure using
        the given path, then build the feature tree path as rev_folder + structure key.
        Returns (Path or None, error_message or None, product_type or None).
        """
        try:
            from harnice import state

            rev_folder = os.path.normpath(os.path.abspath(folder))
            part_dir = os.path.dirname(rev_folder)
            rev_name = os.path.basename(rev_folder)
            part_name = os.path.basename(part_dir)

            if not rev_name.startswith(f"{part_name}-rev"):
                raise RuntimeError(f"Not a revision folder: {rev_folder}")
            suffix = rev_name.split("-rev", 1)[-1]
            if not suffix:
                raise RuntimeError(f"Not a revision folder: {rev_folder}")

            state.set_pn(part_name)
            state.set_rev(int(suffix) if suffix.isdigit() else suffix)

            rev_hist_path = os.path.join(part_dir, f"{part_name}-revision_history.tsv")
            if not os.path.exists(rev_hist_path):
                raise RuntimeError(f"Revision history not found: {rev_hist_path}")

            with open(rev_hist_path, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f, delimiter="\t")
                rows = list(reader)

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

            if not product_type:
                raise RuntimeError(f"No product type for revision folder: {rev_folder}")

            product_module = __import__(
                f"harnice.products.{product_type}", fromlist=[product_type]
            )
            if not hasattr(product_module, "file_structure"):
                raise RuntimeError(f"Product '{product_type}' has no file_structure()")

            structure = product_module.file_structure()
            state.set_file_structure(structure)
            path_parts = _find_feature_tree_path_in_structure(structure)
            if not path_parts:
                raise RuntimeError(
                    f"Product '{product_type}' file_structure has no 'feature tree' entry"
                )

            full_path = os.path.join(rev_folder, *path_parts)
            return Path(full_path), None, product_type
        except Exception as e:
            return None, str(e), None

    @property
    def rev_folder(self) -> str:
        with self.lock:
            return self._rev_folder

    @property
    def product_type(self):
        with self.lock:
            return self._product_type

    @property
    def editor_files(self):
        with self.lock:
            return list(self._editor_files)

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
# console state file — remembered projects
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


def _is_inside_harnice_repo(path: str) -> bool:
    """True if path is the Harnice repo root or any path inside it (don't add as user project)."""
    try:
        from harnice import fileio

        root = fileio.harnice_root()
        path_norm = os.path.normpath(os.path.abspath(path))
        root_norm = os.path.normpath(os.path.abspath(root))
        return path_norm == root_norm or path_norm.startswith(root_norm + os.sep)
    except Exception:
        return False


def _add_recent_project(rev_folder: str):
    """Add rev_folder to recent projects unless it is inside the Harnice repo (e.g. development)."""
    if _is_inside_harnice_repo(rev_folder):
        return
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


def _set_recent_projects_order(rev_folders: list):
    """Set the order of recent projects (e.g. after user drag). Only reorders existing entries."""
    data = _load_gui_state()
    current = [
        os.path.normpath(os.path.abspath(p)) for p in data.get("recent_projects", [])
    ]
    requested = [os.path.normpath(os.path.abspath(p)) for p in rev_folders if p]
    if set(requested) != set(current) or len(requested) != len(current):
        return False
    data["recent_projects"] = requested[:50]
    _save_gui_state(data)
    return True


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
            "/graph-editor": self._serve_graph_editor_html,
            "/system-list-view.js": self._serve_system_list_view_js,
            "/api/info": self._api_info,
            "/api/code": self._api_get_code,
            "/api/function_index": self._api_function_index,
            "/api/run_output": self._api_run_output,
            "/api/recent_projects": self._api_recent_projects,
            "/api/gui_setup": self._api_gui_setup_get,
            "/api/browse": self._api_browse,
            "/api/available": self._api_graph_available,
            "/api/chosen_list": self._api_graph_chosen_list,
            "/api/chosen_net": self._api_graph_chosen_net,
            "/api/flattened": self._api_graph_flattened,
        }
        handler = routes.get(path)
        if handler:
            handler()
            return
        # System viewer API (system product only)
        if _state.product_type == "system":
            if path == "/api/files":
                system_viewer_server.serve_files(self)
                return
            if path == "/api/sse":
                system_viewer_server.serve_sse(self)
                return
            if path.startswith("/api/channel-type-compatible"):
                system_viewer_server.serve_channel_type_compatible(self)
                return
            if path.startswith("/api/channel-type-display"):
                system_viewer_server.serve_channel_type_display(self)
                return
            if path.startswith("/api/signals-list"):
                system_viewer_server.serve_signals_list(self)
                return
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
            "/api/reorder_projects": self._api_reorder_projects,
            "/api/gui_setup": self._api_gui_setup_post,
            "/api/close": self._api_close,
            "/api/available": self._api_graph_save_available,
            "/api/chosen_list": self._api_graph_save_chosen_list,
            "/api/flattened": self._api_graph_save_flattened,
        }
        handler = routes.get(path)
        if handler:
            handler()
        else:
            self.send_error(404)

    # ---- GET handlers ----

    def _serve_html(self):
        if not _EDITOR_HTML.exists():
            self.send_error(500, "harnice_console.html not found")
            return
        self._send_bytes(_EDITOR_HTML.read_bytes(), "text/html; charset=utf-8")

    def _serve_graph_editor_html(self):
        """Serve graph editor HTML for embedding in iframe. Same origin so /api/* go to this server."""
        if not _GRAPH_EDITOR_HTML.exists():
            self.send_error(500, "graph_editor.html not found")
            return
        self._send_bytes(_GRAPH_EDITOR_HTML.read_bytes(), "text/html; charset=utf-8")

    def _serve_system_list_view_js(self):
        """Serve in-DOM system list view script for Harnice console."""
        if not _SYSTEM_LIST_VIEW_JS.exists():
            self.send_error(500, "system_list_view.js not found")
            return
        self._send_bytes(
            _SYSTEM_LIST_VIEW_JS.read_bytes(), "application/javascript; charset=utf-8"
        )

    def _api_info(self):
        pn, rev = _state.pn_and_rev()
        p = _state.feature_tree_path
        payload = {
            "part_number": pn,
            "rev": rev,
            "feature_tree_path": str(p) if p else None,
            "rev_folder": _state.rev_folder,
            "product_type": _state.product_type,
            "editor_files": _state.editor_files,
        }
        if _state.product_type == "system":
            try:
                tabs = system_viewer_core.get_tab_list()
                payload["system_list_label_to_key"] = {
                    label: key for (key, label) in tabs
                }
            except Exception:
                payload["system_list_label_to_key"] = {}
        self._send_json(payload)

    def _api_get_code(self):
        try:
            if _state.feature_tree_path is None:
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
            self._send_json({"code": code, "feature_tree_resolved": True})
        except Exception as e:
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
        folders = [
            p for p in data.get("recent_projects", []) if not _is_inside_harnice_repo(p)
        ]
        projects = []
        for rev_folder in folders:
            info = _project_info_for_revision_folder(rev_folder) or {}
            projects.append(
                {
                    "rev_folder": rev_folder,
                    "product_type": (info.get("product_type") or "").strip() or None,
                    "description": (info.get("description") or "").strip() or None,
                    "button_color": info.get("button_color"),
                }
            )
        self._send_json({"projects": projects})

    def _api_gui_setup_get(self):
        """Return persisted GUI setup (e.g. sidebar slider position) from console state file."""
        data = _load_gui_state()
        height = data.get("sidebar_file_navigator_height")
        if height is not None and not isinstance(height, (int, float)):
            height = None
        self._send_json({"sidebar_file_navigator_height": height})

    def _api_gui_setup_post(self):
        """Persist GUI setup (e.g. sidebar slider position) into console state file."""
        try:
            body = self._read_json_body()
        except Exception:
            self._send_json({"error": "Invalid JSON"}, status=400)
            return
        data = _load_gui_state()
        if "sidebar_file_navigator_height" in body:
            v = body["sidebar_file_navigator_height"]
            if v is None:
                data.pop("sidebar_file_navigator_height", None)
            elif isinstance(v, (int, float)) and 0 < v < 10000:
                data["sidebar_file_navigator_height"] = int(round(v))
        _save_gui_state(data)
        self._send_json({"ok": True})

    def _graph_api_guard(self):
        """Return None if graph API is allowed (harness project), else send error and return True."""
        if _state.product_type != "harness":
            self._send_json(
                {"error": "Graph editor is only available for harness projects"},
                status=400,
            )
            return True
        return None

    def _api_graph_available(self):
        if self._graph_api_guard():
            return
        p = _graph_file_path(_state.rev_folder, "harness", "available network")
        data = _graph_read_json(p, {"segments": [], "nodes": []})
        self._send_json(data)

    def _api_graph_save_available(self):
        if self._graph_api_guard():
            return
        body = self._read_json_body()
        p = _graph_file_path(_state.rev_folder, "harness", "available network")
        _graph_write_json(p, body)
        self.send_response(200)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _api_graph_chosen_list(self):
        if self._graph_api_guard():
            return
        p = _graph_file_path(_state.rev_folder, "harness", "chosen entity list")
        data = _graph_read_json(p, [])
        self._send_json(data)

    def _api_graph_save_chosen_list(self):
        if self._graph_api_guard():
            return
        body = self._read_json_body()
        p = _graph_file_path(_state.rev_folder, "harness", "chosen entity list")
        _graph_write_json(p, body)
        self.send_response(200)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _api_graph_chosen_net(self):
        if self._graph_api_guard():
            return
        p = _graph_file_path(_state.rev_folder, "harness", "chosen network")
        data = _graph_read_json(p, None)
        self._send_json(data)

    def _api_graph_flattened(self):
        if self._graph_api_guard():
            return
        p = _graph_file_path(_state.rev_folder, "harness", "flattened network")
        fieldnames, rows = _graph_read_csv(p)
        self._send_json({"fieldnames": fieldnames, "rows": rows})

    def _api_graph_save_flattened(self):
        if self._graph_api_guard():
            return
        body = self._read_json_body()
        fieldnames = body.get("fieldnames", [])
        rows = body.get("rows", [])
        p = _graph_file_path(_state.rev_folder, "harness", "flattened network")
        _graph_write_csv(p, fieldnames, rows)
        self.send_response(200)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _api_browse(self):
        """Show OS folder picker in a subprocess so tkinter runs on a proper main thread (avoids crash when server uses threads)."""
        path = None
        error = None
        try:
            result = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    "import tkinter as tk; from tkinter import filedialog; "
                    "root = tk.Tk(); root.withdraw(); "
                    "s = filedialog.askdirectory(title='Select revision folder'); "
                    "root.destroy(); print(s or '')",
                ],
                capture_output=True,
                text=True,
                timeout=300,
                env={**os.environ},
            )
            raw = (result.stdout or "").strip()
            path = raw if raw else None
            if result.stderr and not path:
                error = result.stderr.strip() or None
        except subprocess.TimeoutExpired:
            error = "Folder picker timed out"
        except Exception as e:
            error = str(e)
        self._send_json({"path": path, "error": error})

    # ---- POST handlers ----

    def _api_post_code(self):
        """Save feature tree code. Rejects request when content is empty/placeholder or
        rev_folder does not match current project (see guards below).
        """
        body = self._read_json_body()
        code = body.get("code", "")
        # Guard 1: Refuse empty or placeholder content (avoids accidental overwrite when
        # editor shows "feature tree not found" or when content was never loaded).
        if not code or not code.strip():
            self._send_json(
                {
                    "ok": False,
                    "error": "Refusing to save empty content to feature tree",
                },
                status=400,
            )
            return
        if code.strip().startswith("feature tree not found"):
            self._send_json(
                {
                    "ok": False,
                    "error": "Refusing to save placeholder text; load a project with a feature tree first",
                },
                status=400,
            )
            return
        # Guard 2: Require rev_folder to match current project (prevents multi-tab / stale tab
        # from writing one project's buffer into another project's file).
        rev_folder = (body.get("rev_folder") or "").strip()
        current = (getattr(_state, "rev_folder", None) or "").strip()
        if not current:
            self._send_json(
                {"ok": False, "error": "No project selected on server"},
                status=400,
            )
            return
        norm = os.path.normpath
        if not rev_folder or norm(os.path.abspath(rev_folder)) != norm(
            os.path.abspath(current)
        ):
            self._send_json(
                {
                    "ok": False,
                    "error": "Project mismatch; switch to this project again and save",
                },
                status=400,
            )
            return
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
        pn, rev = _state.pn_and_rev()
        p = _state.feature_tree_path
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
        if not folder or not os.path.isdir(folder):
            self._send_json({"ok": False, "error": "invalid folder"}, status=400)
            return
        _add_recent_project(folder)
        self._send_json({"ok": True})

    def _api_select_project(self):
        """Run fileio.verify_revision_structure() in a subprocess with cwd=rev_folder; kill any running harnice -r; return exit_code and output for the console. Client should then switch + load code if exit_code is 0."""
        body = self._read_json_body()
        folder = body.get("rev_folder", "").strip()
        if not folder or not os.path.isdir(folder):
            self._send_json({"ok": False, "error": "invalid folder"}, status=400)
            return
        folder = os.path.normpath(os.path.abspath(folder))

        _stop_run(_state)

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
        except Exception as e:
            exit_code = -1
            stdout = ""
            stderr = str(e)

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

    def _api_reorder_projects(self):
        body = self._read_json_body()
        rev_folders = body.get("rev_folders", [])
        if not isinstance(rev_folders, list):
            self._send_json(
                {"ok": False, "error": "rev_folders must be a list"}, status=400
            )
            return
        if _set_recent_projects_order(rev_folders):
            self._send_json({"ok": True})
        else:
            self._send_json(
                {"ok": False, "error": "invalid order (must match existing projects)"},
                status=400,
            )

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
    # Start system viewer file watcher so embedded system list panes get SSE updates
    system_viewer_core.start_file_watcher()
    # Purge any Harnice-repo paths from saved recent projects so they don't reappear
    data = _load_gui_state()
    cleaned = [
        p for p in data.get("recent_projects", []) if not _is_inside_harnice_repo(p)
    ]
    if len(cleaned) != len(data.get("recent_projects", [])):
        data["recent_projects"] = cleaned
        _save_gui_state(data)

    class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
        daemon_threads = True

    server = ThreadedHTTPServer(("127.0.0.1", port), FeatureTreeHandler)
    actual_port = server.server_address[1]
    url = f"http://127.0.0.1:{actual_port}/"

    # Write URL to env-var file when HARNICE_CONSOLE_URL_FILE is set
    url_file = os.environ.get("HARNICE_CONSOLE_URL_FILE")
    if url_file:
        try:
            Path(url_file).write_text(url, encoding="utf-8")
        except Exception:
            pass

    print(f"Harnice console: {url}  (Ctrl+C to stop)")

    if open_browser:
        webbrowser.open(url)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[server] stopped.")


def main():
    """Entry point for harnice-gui: build function index and launch Harnice console."""
    from harnice.gui.build_feature_tree_gui import build as build_feature_index

    build_feature_index()
    run_server(port=0, open_browser=True)


if __name__ == "__main__":
    folder = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    run_server(rev_folder=folder)
