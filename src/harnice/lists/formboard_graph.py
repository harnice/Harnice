import csv
import os
from harnice import fileio

COLUMNS = [
    "segment_id", # the unique name of the segment that this line describes
    "node_at_end_a", # one of two ends of this segment
    "node_at_end_b", # one of two ends of this segment
    "length", # length of this segment
    "angle", # what angle is the segment visualized on a formboard, with respect to the x axis
    "diameter", # what is the diameter of this segment
]

#TODO; https://github.com/harnice/Harnice/issues/610
# move angle and diameter out of the formboard definition. this list should only describe the part, not the visualization of the part. 


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
