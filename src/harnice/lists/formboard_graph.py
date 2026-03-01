import csv
import os
from harnice import fileio

AVAILABLE_NETWORK: {
    "segments": [
        {
            "segment_id": "name",
            "location_at_end_a": [x,y,z],
            "location_at_end_b": [x,y,z],
            "spline_control_points": [ # from A to B. if this section exists, it must have at least one control point.
            # tangent points and pass-throughs should be defined as entirely different segments that meet up
                [x,y,z],
                [x,y,z]
            ],
            "chosen": True
        }
    ],
    "nodes": [ #optional. this section allows you to specify names or rotations of points in space if you want to
        {
            "node_id": "name",
            "location": [x,y,z],
            "alpha": 0, #optional
            "beta": 0, #optional 
            "gamma": 0, #optional
            "chosen": True
        }
    ]
}


FLATTENED_COLUMNS = [
    "segment_id", # the unique name of the segment that this line describes
    "node_at_end_a", # one of two ends of this segment
    "node_at_end_b", # one of two ends of this segment
    "length", # length of this segment
    "length_tolerance", # string describing length tolerance
    "angle", # what angle is the segment visualized on a formboard, with respect to the x axis
    "diameter", # what is the diameter of this segment
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
