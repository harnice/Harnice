"""
chosen_network.py
Reads available_network.json, resolves chosen segments and nodes, writes chosen_network.json.
"""

from __future__ import annotations
import json
import math
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum

Point3D = tuple[float, float, float]


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

class SegmentType(Enum):
    LINE = "line"
    SPLINE = "spline"


@dataclass
class AvailableNode:
    node_id: str
    location: Point3D
    alpha: Optional[float] = None
    beta: Optional[float] = None
    gamma: Optional[float] = None


@dataclass
class AvailableSegment:
    segment_id: str
    type: SegmentType
    location_at_end_a: Point3D
    location_at_end_b: Point3D
    spline_control_points: list[Point3D] = field(default_factory=list)

    def __post_init__(self):
        if self.type == SegmentType.SPLINE and len(self.spline_control_points) == 0:
            raise ValueError(
                f"Segment '{self.segment_id}': splines must have at least one control point"
            )


@dataclass
class ChosenNode:
    node_id: str
    location: Point3D
    alpha: Optional[float] = None   # TODO: compute default orientation
    beta: Optional[float] = None
    gamma: Optional[float] = None


@dataclass
class ChosenSegment:
    segment_id: str
    length: float
    node_at_end_a: str  # ChosenNode id
    node_at_end_b: str  # ChosenNode id


@dataclass
class ChosenNetwork:
    segments: list[ChosenSegment] = field(default_factory=list)
    nodes: list[ChosenNode] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Math
# ---------------------------------------------------------------------------

def _euclidean(a: Point3D, b: Point3D) -> float:
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def _location_key(p: Point3D, precision: int = 9) -> str:
    return f"{round(p[0], precision)},{round(p[1], precision)},{round(p[2], precision)}"


def _spline_arc_length(points: list[Point3D], samples: int = 100) -> float:
    """Approximate arc length by sampling a Catmull-Rom spline through the points.
    points: [end_a, control_0, ..., end_b]
    """
    if len(points) < 2:
        raise ValueError("Need at least 2 points to compute arc length")
    if len(points) == 2:
        return _euclidean(points[0], points[1])

    def catmull_rom(p0, p1, p2, p3, t):
        return tuple(
            0.5 * ((2 * p1[i])
            + (-p0[i] + p2[i]) * t
            + (2*p0[i] - 5*p1[i] + 4*p2[i] - p3[i]) * t**2
            + (-p0[i] + 3*p1[i] - 3*p2[i] + p3[i]) * t**3)
            for i in range(3)
        )

    padded = [points[0], *points, points[-1]]
    n_segments = len(padded) - 3
    pts_per_segment = max(samples // n_segments, 4)
    total = 0.0

    for i in range(n_segments):
        p0, p1, p2, p3 = padded[i], padded[i+1], padded[i+2], padded[i+3]
        prev = catmull_rom(p0, p1, p2, p3, 0.0)
        for j in range(1, pts_per_segment + 1):
            curr = catmull_rom(p0, p1, p2, p3, j / pts_per_segment)
            total += _euclidean(prev, curr)
            prev = curr

    return total


def _segment_length(seg: AvailableSegment) -> float:
    if seg.type == SegmentType.LINE:
        return _euclidean(seg.location_at_end_a, seg.location_at_end_b)
    return _spline_arc_length([seg.location_at_end_a, *seg.spline_control_points, seg.location_at_end_b])


# ---------------------------------------------------------------------------
# I/O
# ---------------------------------------------------------------------------

def read_available_network(path: Path) -> tuple[list[AvailableSegment], list[AvailableNode]]:
    with open(path, "r") as f:
        data = json.load(f)

    segments = [
        AvailableSegment(
            segment_id=s["segment_id"],
            type=SegmentType(s["type"]),
            location_at_end_a=tuple(s["location_at_end_a"]),
            location_at_end_b=tuple(s["location_at_end_b"]),
            spline_control_points=[tuple(p) for p in s.get("spline_control_points", [])],
        )
        for s in data.get("segments", [])
    ]

    nodes = [
        AvailableNode(
            node_id=n["node_id"],
            location=tuple(n["location"]),
            alpha=n.get("alpha"),
            beta=n.get("beta"),
            gamma=n.get("gamma"),
        )
        for n in data.get("nodes", [])
    ]

    return segments, nodes


def resolve_chosen_network(
    segments: list[AvailableSegment],
    nodes: list[AvailableNode],
    chosen_segment_ids: list[str],
    proximity_threshold: float = 1e-6,
) -> ChosenNetwork:
    chosen_segments = [s for s in segments if s.segment_id in chosen_segment_ids]
    if not chosen_segments:
        raise ValueError("No matching segments found in available network")

    node_registry: dict[str, ChosenNode] = {}  # location_key -> ChosenNode
    auto_counter = 1

    def resolve_endpoint(location: Point3D) -> ChosenNode:
        nonlocal auto_counter
        key = _location_key(location)
        if key in node_registry:
            return node_registry[key]
        for an in nodes:
            if _euclidean(an.location, location) <= proximity_threshold:
                node = ChosenNode(an.node_id, an.location, an.alpha, an.beta, an.gamma)
                node_registry[key] = node
                return node
        node = ChosenNode(f"N{auto_counter}", location)
        auto_counter += 1
        node_registry[key] = node
        return node

    result_segments = []
    for seg in chosen_segments:
        node_a = resolve_endpoint(seg.location_at_end_a)
        node_b = resolve_endpoint(seg.location_at_end_b)
        result_segments.append(ChosenSegment(
            segment_id=seg.segment_id,
            length=_segment_length(seg),
            node_at_end_a=node_a.node_id,
            node_at_end_b=node_b.node_id,
        ))

    return ChosenNetwork(segments=result_segments, nodes=list(node_registry.values()))


def write_chosen_network(network: ChosenNetwork, path: Path) -> None:
    data = {
        "segments": [
            {
                "segment_id": s.segment_id,
                "length": s.length,
                "node_at_end_a": s.node_at_end_a,
                "node_at_end_b": s.node_at_end_b,
            }
            for s in network.segments
        ],
        "nodes": [
            {
                "node_id": n.node_id,
                "location": list(n.location),
                "alpha": n.alpha,
                "beta": n.beta,
                "gamma": n.gamma,
            }
            for n in network.nodes
        ],
    }
    with open(path, "w") as f:
        json.dump(data, f, indent=4)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def build_chosen_network(
    available_path: Path,
    chosen_segment_ids: list[str],
    chosen_path: Path,
    proximity_threshold: float = 1e-6,
) -> ChosenNetwork:
    """Read available_network.json, resolve chosen network, write chosen_network.json."""
    segments, nodes = read_available_network(available_path)
    network = resolve_chosen_network(segments, nodes, chosen_segment_ids, proximity_threshold)
    write_chosen_network(network, chosen_path)
    return network