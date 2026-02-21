"""Centralized tool paths (Inkscape, KiCad CLI) from repo-root paths/paths.json.

Copy paths/paths.example.json to paths/paths.json and adjust for your system.
paths/paths.json is git-ignored.
"""

import json
import os

from harnice import fileio

_DEFAULTS = {
    "inkscape": "/Applications/Inkscape.app/Contents/MacOS/inkscape",
    "kicad_cli": "kicad-cli",
}


def _paths_dir():
    return os.path.join(fileio.harnice_root(), "paths")


def _load_paths():
    """Load paths from paths/paths.json, then paths/paths.example.json, then defaults."""
    base = _paths_dir()
    for name in ("paths.json", "paths.example.json"):
        p = os.path.join(base, name)
        if os.path.isfile(p):
            try:
                with open(p, encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    return {**_DEFAULTS, **data}
            except (json.JSONDecodeError, OSError):
                pass
    return dict(_DEFAULTS)


def get_inkscape_bin():
    """Path to Inkscape executable (for SVG export)."""
    return _load_paths().get("inkscape", _DEFAULTS["inkscape"])


def get_kicad_cli():
    """Path or command name for KiCad CLI (e.g. 'kicad-cli' or full path)."""
    return _load_paths().get("kicad_cli", _DEFAULTS["kicad_cli"])
