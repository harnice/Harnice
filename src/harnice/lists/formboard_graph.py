import csv
import os
from harnice import fileio

COLUMNS = [
    "segment_id",
    "node_at_end_a",
    "node_at_end_b",
    "length",
    "angle",
    "diameter",
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
    if any(row.get("segment_id") == segment_id
           for row in fileio.read_tsv("formboard graph definition")):
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


def remove(segment_id):
    """Remove the row for the given segment_id from the formboard graph definition."""
    if not segment_id:
        raise ValueError("Argument 'segment_id' is blank.")

    path = fileio.path("formboard graph definition")

    # If the file doesn't exist, nothing to remove
    if not os.path.exists(path):
        return False

    rows = fileio.read_tsv("formboard graph definition")

    # Filter out the matching rows
    new_rows = [row for row in rows if row.get("segment_id") != segment_id]

    # If no change, return False (nothing removed)
    if len(new_rows) == len(rows):
        return False

    # Rewrite the file with header + remaining rows
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=COLUMNS, delimiter="\t", lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(new_rows)

    return True
