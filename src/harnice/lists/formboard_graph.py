import csv
import os
from harnice import fileio

COLUMNS = [
    "segment_id", #documentation needed
    "node_at_end_a", #documentation needed
    "node_at_end_b", #documentation needed
    "length", #documentation needed
    "angle", #documentation needed
    "diameter", #documentation needed
]


def new():
    with open(
        fileio.path("formboard graph definition"),
        "w",
        newline="",
        encoding="utf-8",
    ) as f:
        writer = csv.DictWriter(
            f, fieldnames=COLUMNS, delimiter="\t", lineterminator="\n"
        )
        writer.writeheader()


def append(segment_id, segment_data):
    if not segment_id:
        raise ValueError(
            "Argument 'segment_id' is blank and required to identify a unique segment"
        )

    segment_data["segment_id"] = segment_id

    # Prevent duplicates
    if any(
        row.get("segment_id") == segment_id
        for row in fileio.read_tsv("formboard graph definition")
    ):
        return True

    # Ensure the file exists
    path = fileio.path("formboard graph definition")
    if not os.path.exists(path):
        new()

    # Append safely
    with open(path, "a+", newline="", encoding="utf-8") as f:
        # ---- Ensure file ends with a newline before writing ----
        f.seek(0, os.SEEK_END)
        if f.tell() > 0:  # file is non-empty
            f.seek(f.tell() - 1)
            if f.read(1) != "\n":
                f.write("\n")
        # --------------------------------------------------------

        writer = csv.DictWriter(
            f, fieldnames=COLUMNS, delimiter="\t", lineterminator="\n"
        )
        writer.writerow({key: segment_data.get(key, "") for key in COLUMNS})

    return False
