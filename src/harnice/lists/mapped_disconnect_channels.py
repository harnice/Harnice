# mapped_disconnect_channels_set.py
import os
from harnice import fileio
from harnice.utils import system_utils


def new_set():
    """Create or reset the file to represent an empty set."""
    with open(fileio.path("mapped disconnect channels set"), "w", encoding="utf-8"):
        pass


def append(item):
    """Add an item to the set (if not already present)."""
    items = return_set()
    items.add(str(item))
    _write(items)


def check(item):
    """Return True if item is in the set, False otherwise."""
    return str(item) in return_set()


def return_set():
    """Return the full set of items."""
    path = fileio.path("mapped disconnect channels set")
    if not os.path.exists(path):
        return set()
    with open(path, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f if line.strip())


def _write(items):
    """Internal: write a set of items to file."""
    path = fileio.path("mapped disconnect channels set")
    with open(path, "w", encoding="utf-8") as f:
        for item in sorted(items):
            f.write(f"{item}\n")

def map_and_record_disconnect(a_side_key, disconnect_key):
    system_utils.map_channel_to_disconnect_channel(a_side_key, disconnect_key)
    append(disconnect_key)