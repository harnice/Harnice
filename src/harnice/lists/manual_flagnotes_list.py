import os
import csv
from harnice import fileio

COLUMNS = [
    "note_type",
    "note_text",
    "shape",
    "shape_lib_repo",
    "bubble_text",
    "affectedinstances",
]

def ensure_exists():
    if not os.path.exists(fileio.path("flagnotes manual")):
        with open(
            fileio.path("flagnotes manual"), "w", newline="", encoding="utf-8"
        ) as f:
            writer = csv.DictWriter(
                f, fieldnames=COLUMNS, delimiter="\t"
            )
            writer.writeheader()
