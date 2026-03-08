"""
Thin HTTP layer for system list API (system product).
Uses system_viewer_core for data, tab list, and SSE watcher.
feature_tree_server imports serve_files, serve_sse, serve_channel_type_*,
serve_signals_list and uses them for /api/files, /api/sse, etc. when product_type is system.
"""

import http.server
import json
import queue
import socketserver
import webbrowser
from pathlib import Path

from urllib.parse import parse_qs, urlparse

from harnice.gui import system_viewer_core
from harnice.products import chtype


def _viewer_html_path():
    return Path(__file__).resolve().parent / "system_viewer.html"


class SystemViewerHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        if self.path.split("?")[0] in ("/", "/index.html"):
            self._serve_viewer()
        elif self.path.split("?")[0] == "/api/files":
            self._serve_files()
        elif self.path.split("?")[0] == "/api/sse":
            self._serve_sse()
        elif self.path.startswith("/api/channel-type-compatible"):
            self._serve_channel_type_compatible()
        elif self.path.startswith("/api/channel-type-display"):
            self._serve_channel_type_display()
        elif self.path.startswith("/api/signals-list"):
            self._serve_signals_list()
        else:
            self.send_error(404)

    def _serve_viewer(self):
        serve_viewer(self)

    def _serve_files(self):
        serve_files(self)

    def _serve_channel_type_compatible(self):
        serve_channel_type_compatible(self)

    def _serve_channel_type_display(self):
        serve_channel_type_display(self)

    def _serve_signals_list(self):
        serve_signals_list(self)

    def _serve_sse(self):
        serve_sse(self)


def start_file_watcher():
    """Start the background file watcher (for SSE). Re-export from core."""
    system_viewer_core.start_file_watcher()


def get_system_viewer_tab_list():
    """Return list of (file_key, display_label) for feature tree editor. Re-export from core."""
    return system_viewer_core.get_tab_list()


def serve_viewer(handler):
    """Serve system_viewer.html. handler must have send_response, send_header, end_headers, wfile."""
    html_path = _viewer_html_path()
    if not html_path.exists():
        handler.send_error(500, "System viewer HTML not found")
        return
    with open(html_path, "rb") as f:
        data = f.read()
    handler.send_response(200)
    handler.send_header("Content-Type", "text/html; charset=utf-8")
    handler.send_header("Content-Length", str(len(data)))
    handler.end_headers()
    handler.wfile.write(data)


def serve_files(handler):
    """Serve GET /api/files JSON."""
    files = system_viewer_core.get_all_files()
    body = json.dumps(files).encode("utf-8")
    handler.send_response(200)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def serve_sse(handler):
    """Serve GET /api/sse event stream."""
    handler.send_response(200)
    handler.send_header("Content-Type", "text/event-stream")
    handler.send_header("Cache-Control", "no-cache")
    handler.send_header("Connection", "keep-alive")
    handler.send_header("X-Accel-Buffering", "no")
    handler.end_headers()

    q = queue.Queue()
    system_viewer_core.subscribe_sse(q)
    try:
        handler.wfile.write(": connected\n\n".encode("utf-8"))
        handler.wfile.flush()
    except (BrokenPipeError, ConnectionResetError, OSError):
        system_viewer_core.unsubscribe_sse(q)
        return

    try:
        while True:
            try:
                item = q.get(timeout=15)
            except queue.Empty:
                try:
                    handler.wfile.write(": keepalive\n\n".encode("utf-8"))
                    handler.wfile.flush()
                except (BrokenPipeError, ConnectionResetError, OSError):
                    break
                continue
            try:
                if len(item) == 3:
                    file_key, label, content = item
                else:
                    file_key, content = item
                    label = system_viewer_core.display_label(file_key)
            except (ValueError, TypeError):
                continue
            try:
                payload = json.dumps(
                    {"key": file_key, "label": label, "content": content}
                )
                handler.wfile.write(f"data: {payload}\n\n".encode("utf-8"))
                handler.wfile.flush()
            except (BrokenPipeError, ConnectionResetError, OSError):
                break
    finally:
        system_viewer_core.unsubscribe_sse(q)


def serve_channel_type_compatible(handler):
    """Serve GET /api/channel-type-compatible."""
    parsed = urlparse(handler.path)
    params = parse_qs(parsed.query)
    type_str = (params.get("type") or [None])[0]
    if not type_str:
        handler.send_response(400)
        handler.send_header("Content-Type", "application/json; charset=utf-8")
        handler.end_headers()
        handler.wfile.write(b'{"error": "missing type parameter"}')
        return
    try:
        allowed = chtype.is_or_is_compatible_with(type_str)
        out = [repr(t) for t in allowed if t is not None]
    except Exception:
        handler.send_response(200)
        handler.send_header("Content-Type", "application/json; charset=utf-8")
        handler.end_headers()
        handler.wfile.write(json.dumps([type_str]).encode("utf-8"))
        return
    handler.send_response(200)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    body = json.dumps(out).encode("utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def serve_channel_type_display(handler):
    """Serve GET /api/channel-type-display."""
    parsed = urlparse(handler.path)
    params = parse_qs(parsed.query)
    types = params.get("type") or []
    result = {}
    for type_str in types:
        if not type_str or not type_str.strip():
            continue
        type_str = type_str.strip()
        try:
            desc = chtype.attribute(type_str, "description")
            direction = chtype.attribute(type_str, "direction")
            if desc == [] or desc is None:
                desc = ""
            if direction == [] or direction is None:
                direction = ""
            desc = str(desc).strip()
            direction = str(direction).strip()
            if direction:
                result[type_str] = f"{desc} ({direction})" if desc else f"({direction})"
            else:
                result[type_str] = desc or type_str
        except Exception:
            result[type_str] = type_str
    body = json.dumps(result).encode("utf-8")
    handler.send_response(200)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def serve_signals_list(handler):
    """Serve GET /api/signals-list."""
    parsed = urlparse(handler.path)
    params = parse_qs(parsed.query)
    refdes = (params.get("device_refdes") or [None])[0]
    content, error = system_viewer_core.get_signals_list_content(refdes or "")
    if error:
        status = 400 if "missing" in error or "invalid" in error else 500
        handler.send_response(status)
        handler.send_header("Content-Type", "text/plain; charset=utf-8")
        handler.end_headers()
        handler.wfile.write(error.encode("utf-8"))
        return
    handler.send_response(200)
    handler.send_header("Content-Type", "text/tab-separated-values; charset=utf-8")
    body = content.encode("utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def run_server(port=0, open_browser=True):
    """
    Legacy standalone system viewer server (no longer used; GUI is feature tree only).
    Uses port 0 to pick an ephemeral port.
    """
    start_file_watcher()

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
        pass
