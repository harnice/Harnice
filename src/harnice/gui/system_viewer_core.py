"""
Shared core for system viewer (system product list data, tab list, file watcher, SSE).
Used by the feature tree server (system list panes) and by the standalone system viewer server.
Requires fileio/state to be set (e.g. from feature tree server on project switch, or CLI cwd).
"""

import os
import queue
import re
import threading
import time

from harnice import fileio, state

# Restrict device_refdes to safe characters (no path separators or traversal)
VALID_REFDES_RE = re.compile(r"^[A-Za-z0-9_.-]+$")

# Tab order and display names (file_key -> display label)
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


def display_label(file_key):
    """Return the display label for a file key (tab text)."""
    if file_key in TAB_DISPLAY_LABELS:
        return TAB_DISPLAY_LABELS[file_key]
    return file_key.replace("_", " ").title()


def read_file_content(file_key):
    """Return raw file content for a file key, or empty string if missing."""
    try:
        path = fileio.path(file_key)
    except (TypeError, Exception):
        return ""
    if not path or not os.path.isfile(path):
        return ""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except OSError:
        return ""


def get_all_files():
    """Return dict of file_key -> { content, label } for tabs. Requires state to be set."""
    try:
        structure = state.file_structure
    except (NameError, AttributeError):
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
            "content": read_file_content(key),
            "label": display_label(key),
        }
        for key in ordered
    }


def get_tab_list():
    """
    Return list of (file_key, display_label) for tabs that exist in the current project.
    Used by the feature tree editor to build the project files selector for system products.
    """
    files = get_all_files()
    ordered = [k for k in TAB_ORDER if k in files]
    if (
        "post harness instances list" in files
        and "post harness instances list" not in ordered
    ):
        ordered.append("post harness instances list")
    return [(key, files[key]["label"]) for key in ordered]


# SSE: queues and watcher shared by all servers
_sse_queues = []
_sse_lock = threading.Lock()
_watcher_stop = threading.Event()
_watcher_started = False


def _file_watcher_loop():
    """Background thread: poll file mtimes and push updates to all SSE clients."""
    last_mtimes = {}
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
                    content = read_file_content(file_key)
                    label = display_label(file_key)
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


def start_file_watcher():
    """Start the background file watcher (for SSE). Safe to call multiple times; only one thread runs."""
    global _watcher_started
    with _sse_lock:
        if _watcher_started:
            return
        _watcher_started = True
    watcher = threading.Thread(target=_file_watcher_loop, daemon=True)
    watcher.start()


def subscribe_sse(queue_obj):
    """Register a queue to receive (file_key, label, content) updates. Call from HTTP SSE handler."""
    with _sse_lock:
        _sse_queues.append(queue_obj)


def unsubscribe_sse(queue_obj):
    """Unregister a queue. Call when SSE connection closes."""
    with _sse_lock:
        if queue_obj in _sse_queues:
            _sse_queues.remove(queue_obj)


def get_signals_list_content(device_refdes):
    """
    Return (content_str, error_str). content_str is TSV body if found; error_str is non-None on failure.
    Requires state/fileio to be set.
    """
    if not device_refdes or not device_refdes.strip():
        return "", "missing device_refdes parameter"
    refdes = device_refdes.strip()
    if not VALID_REFDES_RE.match(refdes) or refdes in (".", ".."):
        return "", "invalid device_refdes parameter"
    try:
        base = os.path.abspath(fileio.dirpath("instance_data"))
        base_with_sep = base if base.endswith(os.sep) else base + os.sep
        for kind in ("device", "disconnect"):
            candidate = os.path.join(base, kind, refdes, f"{refdes}-signals_list.tsv")
            resolved = os.path.abspath(candidate)
            if not resolved.startswith(base_with_sep):
                continue
            if os.path.isfile(resolved):
                with open(resolved, "r", encoding="utf-8") as f:
                    return f.read(), None
        return "", "Signals list not found for this device"
    except (TypeError, OSError) as e:
        return "", str(e)
