"""
Minimal HTTP server for the formboard graph editor.
Serves the graph editor HTML and GET/POST /api/tsv for the revision's formboard graph definition.
Must be run after fileio state is set (e.g. from CLI in a revision directory).
"""

import http.server
import os
import threading
import webbrowser
from pathlib import Path

from harnice import fileio

# Default TSV header when file does not exist (matches formboard_graph.COLUMNS)
_TSV_HEADER = "segment_id\tnode_at_end_a\tnode_at_end_b\tlength\tangle\tdiameter\n"


def _editor_html_path():
    return Path(__file__).resolve().parent / "graph_editor.html"


def _tsv_path():
    return fileio.path("formboard graph definition")


class GraphEditorHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Quiet by default; override to reduce noise
        pass

    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self._serve_editor()
        elif self.path == "/api/tsv":
            self._serve_tsv()
        elif self.path == "/api/close":
            self._close_server()
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path == "/api/tsv":
            self._save_tsv()
        elif self.path == "/api/close":
            self._close_server()
        else:
            self.send_error(404)

    def _serve_editor(self):
        html_path = _editor_html_path()
        if not html_path.exists():
            self.send_error(500, "Graph editor HTML not found")
            return
        with open(html_path, "rb") as f:
            data = f.read()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _serve_tsv(self):
        path = _tsv_path()
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = f.read()
        else:
            data = _TSV_HEADER
        body = data.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/tab-separated-values; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _save_tsv(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8")
        path = _tsv_path()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write(body)
        self.send_response(200)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _close_server(self):
        """Send 200 then shut down the server so serve_forever() returns."""
        self.send_response(200)
        self.send_header("Content-Length", "0")
        self.end_headers()

        def shutdown():
            self.server.shutdown()

        threading.Thread(target=shutdown, daemon=True).start()


def run_server(port=0, open_browser=True):
    """
    Run the graph editor server and optionally open the default browser.
    Uses port 0 to pick an ephemeral port; returns the actual port.
    """
    server = http.server.HTTPServer(("127.0.0.1", port), GraphEditorHandler)
    actual_port = server.server_address[1]
    url = f"http://127.0.0.1:{actual_port}/"
    if open_browser:
        webbrowser.open(url)
    print(f"Graph editor: {url}")
    print("Press Ctrl+C to stop the server.")
    server.serve_forever()
