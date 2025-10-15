import os
from harnice import fileio, instances_list, circuit_instance

artifact_mpn = "circuit_visualizer"

delta_y = 24
node_pointsize = 6
overall_length = 768
whitespace_length = 24

# =============== GLOBAL FONT/STYLING ===============
FONT_FAMILY = "Arial"
FONT_SIZE = 8
FONT_COLOR = "black"

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
    """Draw a node as a filled circle with its instance name aligned horizontally."""
    node_name = node_instance.get("instance_name", "")
    cx = x + node_pointsize / 2
    cy = y

    # Node as filled circle
    circle = f'<circle cx="{cx}" cy="{cy}" r="{node_pointsize/2}" fill="white" stroke="black" stroke-width="1"/>'

    # Label aligned at a consistent vertical level
    label_y = y + node_pointsize + 8
    label = (
        f'<text x="{cx}" y="{label_y}" fill="{FONT_COLOR}" '
        f'text-anchor="middle" font-family="{FONT_FAMILY}" '
        f'font-size="{FONT_SIZE}">{node_name}</text>'
    )

    svg_elements.append(circle)
    svg_elements.append(label)


def plot_segment(segment_instance, x, y, length):
    """Draw a segment as a solid black rectangle (no border)."""
    segment_name = segment_instance.get("instance_name", "")
    rect_height = 2

    # Solid black rectangle
    rect = f'<rect x="{x}" y="{y - rect_height/2}" width="{length}" height="{rect_height}" fill="black"/>'

    # Label aligned at the same vertical level as nodes
    label_y = y + node_pointsize + 8
    label_x = x + (length / 2)
    label = (
        f'<text x="{label_x}" y="{label_y}" fill="{FONT_COLOR}" '
        f'text-anchor="middle" font-family="{FONT_FAMILY}" '
        f'font-size="{FONT_SIZE}">{segment_name}</text>'
    )

    svg_elements.append(rect)
    svg_elements.append(label)


# =============== MAIN LOOP ===============
y = 0
for instance in instances_list.read_instance_rows():
    if instance.get("item_type") != "Circuit":
        continue

    circuit_id = instance.get("circuit_id")
    ports = circuit_instance.instances_of_circuit(circuit_id)

    # Count nodes and segments
    nodes = [p for p in ports if p.get("location_is_node_or_segment") == "Node"]
    segments = [p for p in ports if p.get("location_is_node_or_segment") == "Segment"]

    num_nodes = len(nodes)
    num_segments = len(segments)

    delta_x = 0  # only used if there are no segments
    try:
        segment_length = (overall_length - (num_nodes + num_segments) * whitespace_length) / num_segments
    except ZeroDivisionError:
        delta_x = overall_length / num_nodes
        pass

    x = 0
    for port in ports:
        item_type = port.get("item_type")

        if item_type == "Connector cavity":
            plot_node(port, x, y)
            x += whitespace_length + delta_x
        elif item_type == "Conductor":
            plot_segment(port, x, y, segment_length)
            x += segment_length + whitespace_length

    y += delta_y


# =============== WRITE SVG ===============
output_path = path("circuit visualizer svg")
os.makedirs(os.path.dirname(output_path), exist_ok=True)

with open(output_path, "w", encoding="utf-8") as f:
    f.write(SVG_HEADER)
    f.write(f'<g id="{artifact_id}-circuit-visualizer-contents-start">\n')

    for element in svg_elements:
        f.write(f"  {element}\n")

    f.write("</g>\n")
    f.write(f'<g id="{artifact_id}-circuit-visualizer-contents-end"/>\n')
    f.write(SVG_FOOTER)
