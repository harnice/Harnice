"""
Minimal HTTP server for the TSV/CSV viewer (e.g. system product lists).
Serves the viewer HTML, GET /api/files (all TSV/CSV from file_structure), and GET /api/sse (live updates).
Must be run after fileio state is set (e.g. from CLI in a revision directory).
"""

import http.server
import json
import os
import queue
import threading
import time
import webbrowser
from pathlib import Path

from harnice import fileio, state


def _tsv_file_keys_from_structure(structure_dict):
    """Recursively collect file keys for entries whose key ends with .tsv or .csv."""
    keys = []

    def walk(data):
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, str) and (
                    key.endswith(".tsv") or key.endswith(".csv")
                ):
                    keys.append(value)
                else:
                    walk(value)
        elif isinstance(data, list):
            for item in data:
                walk(item)

    walk(structure_dict)
    return keys


def _read_file_content(file_key):
    """Return raw file content for a file key, or a single header line if missing."""
    try:
        path = fileio.path(file_key)
    except TypeError:
        return ""
    if not os.path.isfile(path):
        return ""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except OSError:
        return ""


def _get_all_files():
    """Return dict of label -> content for all TSV/CSV files in current file_structure."""
    try:
        structure = state.file_structure
    except NameError:
        return {}
    keys = _tsv_file_keys_from_structure(structure)
    return {label: _read_file_content(label) for label in keys}


# SSE: list of queues; watcher pushes (label, content); each client thread blocks on its queue
_sse_queues = []
_sse_lock = threading.Lock()
_watcher_stop = threading.Event()


def _file_watcher_loop():
    """Background thread: poll file mtimes and push updates to all SSE clients."""
    last_mtimes = {}  # path -> mtime
    while not _watcher_stop.is_set():
        try:
            structure = state.file_structure
        except NameError:
            time.sleep(1.5)
            continue
        keys = _tsv_file_keys_from_structure(structure)
        for file_key in keys:
            try:
                path = fileio.path(file_key)
            except TypeError:
                continue
            if not path:
                continue
            try:
                mtime = os.path.getmtime(path) if os.path.isfile(path) else 0
            except OSError:
                mtime = 0
            if path in last_mtimes and last_mtimes[path] != mtime:
                content = _read_file_content(file_key)
                with _sse_lock:
                    for q in _sse_queues:
                        try:
                            q.put((file_key, content))
                        except Exception:
                            pass
            last_mtimes[path] = mtime
        time.sleep(1.5)


def _viewer_html_path():
    return Path(__file__).resolve().parent / "tsv_viewer.html"


class TSVViewerHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self._serve_viewer()
        elif self.path == "/api/files":
            self._serve_files()
        elif self.path == "/api/sse":
            self._serve_sse()
        else:
            self.send_error(404)

    def _serve_viewer(self):
        html_path = _viewer_html_path()
        if not html_path.exists():
            self.send_error(500, "TSV viewer HTML not found")
            return
        with open(html_path, "rb") as f:
            data = f.read()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _serve_files(self):
        files = _get_all_files()
        body = json.dumps(files).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _serve_sse(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.send_header("X-Accel-Buffering", "no")
        self.end_headers()

        q = queue.Queue()
        with _sse_lock:
            _sse_queues.append(q)
        try:
            while True:
                try:
                    label, content = q.get(timeout=30)
                except queue.Empty:
                    # Send comment keepalive
                    try:
                        self.wfile.write(": keepalive\n\n".encode("utf-8"))
                        self.wfile.flush()
                    except (BrokenPipeError, ConnectionResetError, OSError):
                        break
                    continue
                try:
                    payload = json.dumps({"label": label, "content": content})
                    self.wfile.write(f"data: {payload}\n\n".encode("utf-8"))
                    self.wfile.flush()
                except (BrokenPipeError, ConnectionResetError, OSError):
                    break
        finally:
            with _sse_lock:
                if q in _sse_queues:
                    _sse_queues.remove(q)


def run_server(port=0, open_browser=True):
    """
    Run the TSV viewer server and optionally open the default browser.
    Uses port 0 to pick an ephemeral port; returns the actual port.
    """
    watcher = threading.Thread(target=_file_watcher_loop, daemon=True)
    watcher.start()

    server = http.server.HTTPServer(("127.0.0.1", port), TSVViewerHandler)
    actual_port = server.server_address[1]
    url = f"http://127.0.0.1:{actual_port}/"
    if open_browser:
        webbrowser.open(url)
    print(f"TSV viewer: {url}")
    print("Press Ctrl+C to stop the server.")
    try:
        server.serve_forever()
    finally:
        _watcher_stop.set()
