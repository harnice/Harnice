"""
Minimal HTTP server for the system viewer (system product lists).
Serves the viewer HTML, GET /api/files (allowed tabs from file_structure), and GET /api/sse (live updates).
Must be run after fileio state is set (e.g. from CLI in a revision directory).
"""

import http.server
import json
import os
import queue
import re
import socketserver
import threading
import time
import webbrowser
from pathlib import Path

from urllib.parse import parse_qs, urlparse

from harnice import fileio, state
from harnice.products import chtype

# Restrict device_refdes to safe characters (no path separators or traversal)
_VALID_REFDES_RE = re.compile(r"^[A-Za-z0-9_.-]+$")


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


# Tab order and display names for the left tab bar (file_key -> display label)
TAB_ORDER = [
    "instances list",
    "bom",
    "circuits list",
    "harness manifest",
    "channel map",
    "disconnect map",
]
TAB_DISPLAY_LABELS = {
    "instances list": "Instances Lists",
    "bom": "Devices",
    "circuits list": "Circuits",
    "harness manifest": "Harnesses",
    "channel map": "Channel Map",
    "disconnect map": "Disconnect Map",
}


def _display_label(file_key):
    """Return the display label for a file key (tab text)."""
    if file_key in TAB_DISPLAY_LABELS:
        return TAB_DISPLAY_LABELS[file_key]
    # Fallback: title-case the key (e.g. "library history" -> "Library History")
    return file_key.replace("_", " ").title()


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
    """Return dict of file_key -> { content, label } for tabs and instances-list alternates."""
    try:
        structure = state.file_structure
    except NameError:
        return {}
    raw_keys = _tsv_file_keys_from_structure(structure)
    ordered = [k for k in TAB_ORDER if k in raw_keys]
    if (
        "post harness instances list" in raw_keys
        and "post harness instances list" not in ordered
    ):
        ordered.append("post harness instances list")
    return {
        key: {
            "content": _read_file_content(key),
            "label": _display_label(key),
        }
        for key in ordered
    }


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
        except (NameError, AttributeError):
            time.sleep(1.5)
            continue
        try:
            raw_keys = _tsv_file_keys_from_structure(structure)
            keys = [k for k in TAB_ORDER if k in raw_keys]
            if (
                "post harness instances list" in raw_keys
                and "post harness instances list" not in keys
            ):
                keys.append("post harness instances list")
        except Exception:
            time.sleep(1.5)
            continue
        for file_key in keys:
            try:
                path = fileio.path(file_key)
            except (TypeError, Exception):
                continue
            if not path:
                continue
            try:
                mtime = os.path.getmtime(path) if os.path.isfile(path) else 0
            except OSError:
                mtime = 0
            if path in last_mtimes and last_mtimes[path] != mtime:
                try:
                    content = _read_file_content(file_key)
                    label = _display_label(file_key)
                except Exception:
                    continue
                with _sse_lock:
                    for q in _sse_queues:
                        try:
                            q.put((file_key, label, content))
                        except Exception:
                            pass
            last_mtimes[path] = mtime
        time.sleep(1.5)


def _viewer_html_path():
    return Path(__file__).resolve().parent / "system_viewer.html"


class SystemViewerHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self._serve_viewer()
        elif self.path == "/api/files":
            self._serve_files()
        elif self.path == "/api/sse":
            self._serve_sse()
        elif self.path.startswith("/api/channel-type-compatible"):
            self._serve_channel_type_compatible()
        elif self.path.startswith("/api/signals-list"):
            self._serve_signals_list()
        else:
            self.send_error(404)

    def _serve_viewer(self):
        html_path = _viewer_html_path()
        if not html_path.exists():
            self.send_error(500, "System viewer HTML not found")
            return
        with open(html_path, "rb") as f:
            data = f.read()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _serve_files(self):
        files = _get_all_files()  # file_key -> { content, label }
        body = json.dumps(files).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _serve_channel_type_compatible(self):
        """GET /api/channel-type-compatible?type=... returns JSON list of channel type strings (type + compatibles)."""
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        type_str = (params.get("type") or [None])[0]
        if not type_str:
            self.send_response(400)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(b'{"error": "missing type parameter"}')
            return
        try:
            allowed = chtype.is_or_is_compatible_with(type_str)
            # Return string forms that match TSV storage (repr of tuple)
            out = [repr(t) for t in allowed if t is not None]
        except Exception:
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps([type_str]).encode("utf-8"))
            return
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        body = json.dumps(out).encode("utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _serve_signals_list(self):
        """GET /api/signals-list?device_refdes=... returns TSV content.
        Looks under instance_data/device/{refdes}/ first, then instance_data/disconnect/{refdes}/."""
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        refdes = (params.get("device_refdes") or [None])[0]
        if not refdes or not refdes.strip():
            self.send_response(400)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"missing device_refdes parameter")
            return
        refdes = refdes.strip()
        if not _VALID_REFDES_RE.match(refdes) or refdes in (".", ".."):
            self.send_response(400)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"invalid device_refdes parameter")
            return
        try:
            base = os.path.abspath(fileio.dirpath("instance_data"))
            path = None
            for kind in ("device", "disconnect"):
                candidate = os.path.join(
                    base, kind, refdes, f"{refdes}-signals_list.tsv"
                )
                resolved = os.path.abspath(candidate)
                if os.path.commonpath([base, resolved]) != base:
                    continue
                if os.path.isfile(resolved):
                    path = resolved
                    break
            if path is None:
                self.send_response(404)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.end_headers()
                self.wfile.write(
                    f"signals list not found for device or disconnect {refdes}".encode(
                        "utf-8"
                    )
                )
                return
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
        except (TypeError, OSError) as e:
            self.send_response(500)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(str(e).encode("utf-8"))
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/tab-separated-values; charset=utf-8")
        body = content.encode("utf-8")
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
        # Send an immediate keepalive so the client sees activity (avoids ~30s "reconnecting")
        try:
            self.wfile.write(": connected\n\n".encode("utf-8"))
            self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError, OSError):
            with _sse_lock:
                if q in _sse_queues:
                    _sse_queues.remove(q)
            return

        try:
            while True:
                try:
                    item = q.get(timeout=15)
                except queue.Empty:
                    # Send comment keepalive every 15s so the client doesn't think the connection died
                    try:
                        self.wfile.write(": keepalive\n\n".encode("utf-8"))
                        self.wfile.flush()
                    except (BrokenPipeError, ConnectionResetError, OSError):
                        break
                    continue
                # Support both (file_key, content) and (file_key, label, content)
                try:
                    if len(item) == 3:
                        file_key, label, content = item
                    else:
                        file_key, content = item
                        label = _display_label(file_key)
                except (ValueError, TypeError):
                    continue
                try:
                    payload = json.dumps(
                        {"key": file_key, "label": label, "content": content}
                    )
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
    Run the system viewer server and optionally open the default browser.
    Uses port 0 to pick an ephemeral port; returns the actual port.
    """
    watcher = threading.Thread(target=_file_watcher_loop, daemon=True)
    watcher.start()

    class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
        daemon_threads = True

    server = ThreadedHTTPServer(("127.0.0.1", port), SystemViewerHandler)
    actual_port = server.server_address[1]
    url = f"http://127.0.0.1:{actual_port}/"
    if open_browser:
        webbrowser.open(url)
    print(f"System viewer: {url}")
    print("Press Ctrl+C to stop the server.")
    try:
        server.serve_forever()
    finally:
        _watcher_stop.set()
