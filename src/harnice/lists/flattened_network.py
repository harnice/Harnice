"""
flattened_network.py
Reads chosen_network.json, exports a skeleton flattened_network.csv for manual layout entry.
"""

from __future__ import annotations
import json
import csv
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

Point2D = tuple[float, float]

CSV_COLUMNS = [
    "segment_id",
    "node_at_end_a",
    "node_at_end_b",
    "length",
    "angle",
    "pos_a_x",
    "pos_a_y",
    "pos_b_x",
    "pos_b_y",
]


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class FlattenedSegment:
    segment_id: str
    node_at_end_a: str
    node_at_end_b: str
    length: float
    angle: Optional[float] = None       # degrees w.r.t. x axis, entered by user
    pos_a: Optional[Point2D] = None     # entered by user
    pos_b: Optional[Point2D] = None     # entered by user


@dataclass
class FlattenedNetwork:
    segments: list[FlattenedSegment] = field(default_factory=list)


# ---------------------------------------------------------------------------
# I/O
# ---------------------------------------------------------------------------

def read_chosen_network(path: Path) -> FlattenedNetwork:
    """Read chosen_network.json and return a skeleton FlattenedNetwork."""
    with open(path, "r") as f:
        data = json.load(f)

    segments = [
        FlattenedSegment(
            segment_id=s["segment_id"],
            node_at_end_a=s["node_at_end_a"],
            node_at_end_b=s["node_at_end_b"],
            length=s["length"],
        )
        for s in data.get("segments", [])
    ]

    return FlattenedNetwork(segments=segments)


def read_flattened_network(path: Path) -> FlattenedNetwork:
    """Read a previously saved flattened_network.csv, including any user-entered layout data."""
    segments = []
    with open(path, "r", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            segments.append(FlattenedSegment(
                segment_id=row["segment_id"],
                node_at_end_a=row["node_at_end_a"],
                node_at_end_b=row["node_at_end_b"],
                length=float(row["length"]),
                angle=float(row["angle"]) if row["angle"] else None,
                pos_a=(float(row["pos_a_x"]), float(row["pos_a_y"]))
                      if row["pos_a_x"] and row["pos_a_y"] else None,
                pos_b=(float(row["pos_b_x"]), float(row["pos_b_y"]))
                      if row["pos_b_x"] and row["pos_b_y"] else None,
            ))
    return FlattenedNetwork(segments=segments)


def write_flattened_network(network: FlattenedNetwork, path: Path) -> None:
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for s in network.segments:
            writer.writerow({
                "segment_id":    s.segment_id,
                "node_at_end_a": s.node_at_end_a,
                "node_at_end_b": s.node_at_end_b,
                "length":        s.length,
                "angle":         s.angle if s.angle is not None else "",
                "pos_a_x":       s.pos_a[0] if s.pos_a is not None else "",
                "pos_a_y":       s.pos_a[1] if s.pos_a is not None else "",
                "pos_b_x":       s.pos_b[0] if s.pos_b is not None else "",
                "pos_b_y":       s.pos_b[1] if s.pos_b is not None else "",
            })


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def build_flattened_network(chosen_path: Path, flattened_path: Path) -> FlattenedNetwork:
    """Read chosen_network.json and write a skeleton flattened_network.csv."""
    network = read_chosen_network(chosen_path)
    write_flattened_network(network, flattened_path)
    return network