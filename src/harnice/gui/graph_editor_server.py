"""
Minimal HTTP server for the formboard graph editor.
Serves the graph editor HTML and GET/POST /api/tsv for the revision's formboard graph definition.
Must be run after fileio state is set (e.g. from CLI in a revision directory).
"""

import http.server
import json
import os
import threading
import webbrowser
from pathlib import Path

from harnice import fileio

# Default TSV header when file does not exist (matches formboard_graph.COLUMNS)
_TSV_HEADER = "segment_id\tnode_at_end_a\tnode_at_end_b\tlength\tangle\tdiameter\n"


def _pn_and_rev_from_path(rev_folder):
    """
    Return (part_number, rev) for display from a revision folder path,
    e.g. ("MyPart", "rev1"). Returns (None, None) if path doesn't match.
    Same logic as launcher._pn_and_rev_from_path / product_type derivation.
    """
    rev_folder = os.path.normpath(rev_folder)
    part_dir = os.path.dirname(rev_folder)
    rev_folder_name = os.path.basename(rev_folder)
    part_dir_name = os.path.basename(part_dir)
    if not rev_folder_name.startswith(f"{part_dir_name}-rev"):
        return (None, None)
    rev_str = rev_folder_name.split("-rev")[-1]
    if not rev_str.isdigit():
        return (None, None)
    return (part_dir_name, f"rev{rev_str}")


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
        elif self.path == "/api/info":
            self._serve_info()
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

    def _serve_info(self):
        rev_folder = fileio.rev_directory()
        part_number, rev = _pn_and_rev_from_path(rev_folder)
        part_number = part_number if part_number is not None else ""
        rev = rev if rev is not None else ""
        body = json.dumps({"part_number": part_number, "rev": rev}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

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
