"""
available_network.py
Data classes and verification for the available network.
"""

from __future__ import annotations
import json
import math
import random
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum

from harnice import fileio

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
class AvailableNetwork:
    segments: list[AvailableSegment] = field(default_factory=list)
    nodes: list[AvailableNode] = field(default_factory=list)


# ---------------------------------------------------------------------------
# I/O
# ---------------------------------------------------------------------------

def read(path: Path) -> AvailableNetwork:
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

    return AvailableNetwork(segments=segments, nodes=nodes)


def write(network: AvailableNetwork, path: Path) -> None:
    data = {
        "segments": [
            {
                "segment_id": s.segment_id,
                "type": s.type.value,
                "location_at_end_a": list(s.location_at_end_a),
                "location_at_end_b": list(s.location_at_end_b),
                "spline_control_points": [list(p) for p in s.spline_control_points],
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
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _euclidean(a: Point3D, b: Point3D) -> float:
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def _next_segment_id(network: AvailableNetwork) -> str:
    existing = {s.segment_id for s in network.segments}
    counter = 1
    while f"S{counter}" in existing:
        counter += 1
    return f"S{counter}"


# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------

def verify() -> None:
    """
    Cross-references available network segment endpoints against the instances list.
    For any endpoint that has no matching AvailableNode within proximity threshold
    AND no corresponding instance in the instances list, auto-generates a placeholder
    line segment connecting it to the first segment's end A (wheel-spoke, random angle,
    Z=0). Writes the updated network back to disk.
    """
    PROXIMITY_THRESHOLD = 1e-6
    path = Path(fileio.path("available network"))

    if not path.exists():
        write(AvailableNetwork(), path)
        print("verify(): available_network.json not found, created empty file.")

    network = read(path)

    if not network.segments:
        # Seed from instances list — make a spoke for every node instance
        node_instances = [
            i for i in fileio.read_tsv("instances list")
            if i.get("item_type") == "node"
        ]
        if len(node_instances) < 2:
            raise ValueError("Available network has no segments and fewer than 2 node instances to seed from.")
        origin = (0.0, 0.0, 0.0)
        for inst in node_instances:
            seg_id = _next_segment_id(network)
            angle  = random.uniform(0, 2 * math.pi)
            length = random.uniform(6, 18)
            endpoint = (
                round(origin[0] + length * math.cos(angle), 4),
                round(origin[1] + length * math.sin(angle), 4),
                0.0,
            )
            network.segments.append(AvailableSegment(
                segment_id=seg_id,
                type=SegmentType.LINE,
                location_at_end_a=origin,
                location_at_end_b=endpoint,
            ))
            network.nodes.append(AvailableNode(
                node_id=inst.get("instance_name"),
                location=endpoint,
            ))
            print(f"verify(): seeded segment '{seg_id}' for node '{inst.get('instance_name')}'")
        write(network, path)
        return

    # Collect instance names from instances list
    instance_names = {
        instance.get("instance_name")
        for instance in fileio.read_tsv("instances list")
    }

    # Origin is the first segment's end A
    origin = network.segments[0].location_at_end_a

    # Find endpoints with no nearby AvailableNode and no instances list entry
    missing_endpoints: list[Point3D] = []
    for seg in network.segments:
        for endpoint in (seg.location_at_end_a, seg.location_at_end_b):
            matched_node = next(
                (n for n in network.nodes if _euclidean(n.location, endpoint) <= PROXIMITY_THRESHOLD),
                None
            )
            if matched_node is None or matched_node.node_id not in instance_names:
                if endpoint not in missing_endpoints:
                    missing_endpoints.append(endpoint)

    # Auto-generate wheel-spoke line segments for missing endpoints
    for endpoint in missing_endpoints:
        if endpoint == origin:
            continue  # origin doesn't need a spoke to itself

        segment_id = _next_segment_id(network)
        new_segment = AvailableSegment(
            segment_id=segment_id,
            type=SegmentType.LINE,
            location_at_end_a=origin,
            location_at_end_b=(endpoint[0], endpoint[1], 0.0),  # flatten to Z=0
        )
        network.segments.append(new_segment)
        print(f"verify(): auto-generated segment '{segment_id}' for unmatched endpoint {endpoint}")

    write(network, path)