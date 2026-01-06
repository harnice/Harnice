"""
to run...

python3 /Users/kenyonshutt/Documents/GitHub/Harnice/docs_src/docs_compiler.py
"""

import runpy
import time
import sys
import subprocess
from pathlib import Path
from dataclasses import dataclass

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR / "root"
POLL_SECONDS = 0.5


@dataclass(frozen=True)
class Fingerprint:
    mtime_ns: int
    size: int


def iter_py_files(root: Path):
    # deterministic order
    yield from sorted(root.rglob("*.py"))


def fingerprint(path: Path) -> Fingerprint:
    st = path.stat()
    return Fingerprint(mtime_ns=st.st_mtime_ns, size=st.st_size)


def snapshot(root: Path, *, skip_paths: set[Path]) -> dict[Path, Fingerprint]:
    snap: dict[Path, Fingerprint] = {}
    for p in iter_py_files(root):
        rp = p.resolve()
        if rp in skip_paths:
            continue
        if "__pycache__" in rp.parts:
            continue
        try:
            snap[rp] = fingerprint(rp)
        except FileNotFoundError:
            continue
    return snap


def diff(prev: dict[Path, Fingerprint], cur: dict[Path, Fingerprint]):
    changed = [p for p, fp in cur.items() if prev.get(p) != fp]
    deleted = [p for p in prev.keys() if p not in cur]
    changed.sort()
    deleted.sort()
    return changed, deleted


def run_files(paths: list[Path]):
    for p in paths:
        print(f"\n=== run: {p} ===")
        runpy.run_path(str(p), run_name="__main__")


def main() -> int:
    if not ROOT.exists():
        print(f"ROOT does not exist: {ROOT}", file=sys.stderr)
        return 2

    # start mkdocs serve from repo root (where mkdocs.yml lives)
    repo_root = Path(__file__).resolve().parents[1]
    subprocess.Popen(["mkdocs", "serve"], cwd=repo_root)

    this_file = Path(__file__).resolve()
    skip_paths = {this_file}

    prev = snapshot(ROOT, skip_paths=skip_paths)
    print(f"Watching: {ROOT}")
    print(f"Found {len(prev)} .py files. Polling every {POLL_SECONDS}s.")
    print("Press Ctrl-C to stop.\n")

    try:
        while True:
            time.sleep(POLL_SECONDS)
            cur = snapshot(ROOT, skip_paths=skip_paths)
            changed, deleted = diff(prev, cur)

            if changed:
                run_files(changed)

            if deleted:
                for p in deleted:
                    print(f"\n--- deleted: {p} ---")

            prev = cur

    except KeyboardInterrupt:
        print("\nStopped (Ctrl-C).")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
