import csv
import os
import yaml
import xlwt
from harnice import fileio, instances_list, circuit_instance

artifact_mpn = "circuit_visualizer"

delta_y = 24
node_pointsize = 12
overall_length = 768
whitespace_length = 24

# SVG header/footer templates
SVG_HEADER = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg xmlns="http://www.w3.org/2000/svg" version="1.1">
"""
SVG_FOOTER = "</svg>\n"

# Collect all SVG elements here
svg_elements = []


# =============== PATHS ===============
def path(target_value):
    if target_value == "circuit visualizer svg":
        return os.path.join(
            artifact_path,
            f"{fileio.partnumber('pn-rev')}-{artifact_id}-circuit-visualizer-master.svg",
        )
    raise KeyError(f"Filename {target_value} not found in {artifact_mpn} file tree")


# =============== DRAW HELPERS ===============
def plot_node(node_instance, x, y):
    """Draw a node as a circle with its instance name as text."""
    node_name = node_instance.get("instance_name", "")
    cx = x + node_pointsize / 2
    cy = y
    circle = f'<circle cx="{cx}" cy="{cy}" r="{node_pointsize/2}" stroke="black" fill="white" stroke-width="1"/>'
    label = f'<text x="{cx + node_pointsize}" y="{cy + 4}" font-size="10">{node_name}</text>'
    svg_elements.append(circle)
    svg_elements.append(label)


def plot_segment(segment_instance, x, y, length):
    """Draw a segment as a horizontal line."""
    segment_name = segment_instance.get("instance_name", "")
    x1 = x
    x2 = x + length
    y1 = y
    y2 = y
    line = f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="black" stroke-width="1"/>'
    label = f'<text x="{(x1 + x2) / 2}" y="{y1 - 6}" font-size="9" text-anchor="middle">{segment_name}</text>'
    svg_elements.append(line)
    svg_elements.append(label)


# =============== MAIN LOOP ===============
y = 0
for instance in instances_list.read_instance_rows():
    if instance.get("item_type") != "Circuit":
        continue
    print("!!64")

    circuit_id = instance.get("circuit_id")
    ports = circuit_instance.instances_of_circuit(circuit_id)

    # Count nodes and segments
    nodes = [p for p in ports if p.get("location_is_node_or_segment") == "Node"]
    segments = [p for p in ports if p.get("location_is_node_or_segment") == "Segment"]

    num_nodes = len(nodes)
    num_segments = len(segments)
    num_whitespaces = num_nodes + num_segments - 1

    delta_x = 0 #only used if there are no segments
    try:
        segment_length = (overall_length - num_whitespaces * whitespace_length) / num_segments
    except ZeroDivisionError:
        delta_x = overall_length / num_nodes
        pass

    x = 0
    print("!!79")
    for port in ports:
        item_type = port.get("item_type")
        print(f"!!!!!!!!!! plotting {port.get('instance_name')}")
        if item_type == "Connector cavity":
            plot_node(port, x, y)
            x += (whitespace_length + delta_x)
        elif item_type == "Conductor":
            plot_segment(port, x, y, segment_length)
            x += (segment_length + delta_x)

    y += delta_y


# =============== WRITE SVG ===============
output_path = path("circuit visualizer svg")
os.makedirs(os.path.dirname(output_path), exist_ok=True)

with open(output_path, "w", encoding="utf-8") as f:
    f.write(SVG_HEADER)
    for element in svg_elements:
        f.write(f"  {element}\n")
    f.write(SVG_FOOTER)

print(f"SVG written to: {output_path}")
