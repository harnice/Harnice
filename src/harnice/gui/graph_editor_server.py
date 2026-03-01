"""
graph_server.py
HTTP server for the formboard network editor.
Serves the editor HTML and provides REST API for reading/writing network files.
"""

import csv
import http.server
import json
import os
import threading
import webbrowser
from pathlib import Path

from harnice import fileio

# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------

def _available_path():   return Path(fileio.path("available network"))
def _chosen_list_path(): return Path(fileio.path("chosen entity list"))
def _flattened_path():   return Path(fileio.path("flattened network"))
def _chosen_net_path():  return Path(fileio.path("chosen network"))
def _editor_html_path(): return Path(__file__).resolve().parent / "graph_editor.html"

def _pn_and_rev():
    rev_folder = os.path.normpath(fileio.rev_directory())
    part_dir   = os.path.dirname(rev_folder)
    rev_name   = os.path.basename(rev_folder)
    part_name  = os.path.basename(part_dir)
    if not rev_name.startswith(f"{part_name}-rev"):
        return "", ""
    rev_str = rev_name.split("-rev")[-1]
    if not rev_str.isdigit():
        return "", ""
    return part_name, f"rev{rev_str}"

# ---------------------------------------------------------------------------
# File I/O helpers
# ---------------------------------------------------------------------------

def _read_json(path: Path, default):
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default

def _write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def _read_csv(path: Path):
    if not path.exists():
        return [], []
    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return reader.fieldnames or [], list(reader)

def _write_csv(path: Path, fieldnames, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

# ---------------------------------------------------------------------------
# Handler
# ---------------------------------------------------------------------------

class NetworkEditorHandler(http.server.BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        pass  # suppress access log noise

    def do_GET(self):
        routes = {
            "/":                  self._serve_html,
            "/index.html":        self._serve_html,
            "/api/info":          self._serve_info,
            "/api/available":     self._serve_available,
            "/api/chosen_list":   self._serve_chosen_list,
            "/api/chosen_net":    self._serve_chosen_net,
            "/api/flattened":     self._serve_flattened,
        }
        handler = routes.get(self.path)
        if handler:
            handler()
        else:
            self.send_error(404)

    def do_POST(self):
        routes = {
            "/api/available":   self._save_available,
            "/api/chosen_list": self._save_chosen_list,
            "/api/flattened":   self._save_flattened,
            "/api/close":       self._close,
        }
        handler = routes.get(self.path)
        if handler:
            handler()
        else:
            self.send_error(404)

    # ---- GET handlers ----

    def _serve_html(self):
        p = _editor_html_path()
        if not p.exists():
            self.send_error(500, "graph_editor.html not found")
            return
        self._send_bytes(p.read_bytes(), "text/html; charset=utf-8")

    def _serve_info(self):
        pn, rev = _pn_and_rev()
        self._send_json({"part_number": pn, "rev": rev})

    def _serve_available(self):
        data = _read_json(_available_path(), {"segments": [], "nodes": []})
        self._send_json(data)

    def _serve_chosen_list(self):
        data = _read_json(_chosen_list_path(), [])
        self._send_json(data)

    def _serve_chosen_net(self):
        data = _read_json(_chosen_net_path(), None)
        self._send_json(data)  # null if pipeline hasn't run

    def _serve_flattened(self):
        fieldnames, rows = _read_csv(_flattened_path())
        self._send_json({"fieldnames": fieldnames, "rows": rows})

    # ---- POST handlers ----

    def _save_available(self):
        data = self._read_body_json()
        _write_json(_available_path(), data)
        self._send_ok()

    def _save_chosen_list(self):
        data = self._read_body_json()
        _write_json(_chosen_list_path(), data)
        self._send_ok()

    def _save_flattened(self):
        data = self._read_body_json()
        fieldnames = data.get("fieldnames", [])
        rows = data.get("rows", [])
        _write_csv(_flattened_path(), fieldnames, rows)
        self._send_ok()

    def _close(self):
        self._send_ok()
        threading.Thread(target=self.server.shutdown, daemon=True).start()

    # ---- Helpers ----

    def _read_body_json(self):
        length = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def _send_json(self, data):
        body = json.dumps(data).encode("utf-8")
        self._send_bytes(body, "application/json; charset=utf-8")

    def _send_bytes(self, data: bytes, content_type: str):
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_ok(self):
        self.send_response(200)
        self.send_header("Content-Length", "0")
        self.end_headers()

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def run_server(port=0, open_browser=True):
    server = http.server.HTTPServer(("127.0.0.1", port), NetworkEditorHandler)
    port = server.server_address[1]
    url = f"http://127.0.0.1:{port}/"
    if open_browser:
        webbrowser.open(url)
    print(f"Network editor: {url}  (Ctrl+C to stop)")
    server.serve_forever()