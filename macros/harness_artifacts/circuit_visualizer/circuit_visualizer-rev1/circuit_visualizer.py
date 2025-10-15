import os
from harnice import fileio, instances_list, circuit_instance

artifact_mpn = "circuit_visualizer"

# =============== GLOBAL SETTINGS ===============
node_pointsize = 6
overall_length = 480
whitespace_length = 24

# Font and style
FONT_FAMILY = "Arial"
FONT_SIZE = 8
FONT_COLOR = "black"

# Table layout
HEADER_HEIGHT = 16
ROW_HEIGHT = 30
COL1_WIDTH = 72
TABLE_MARGIN_X = 16
TABLE_MARGIN_Y = 16
TABLE_STROKE = "black"
TABLE_FILL = "white"

# Derived layout
COL2_WIDTH = overall_length + 2 * whitespace_length  # right cell width = visualization + margin
VISUALIZATION_INSET_X = whitespace_length            # left inset centers visualization

# SVG header/footer
SVG_HEADER = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg xmlns="http://www.w3.org/2000/svg" version="1.1">
"""
SVG_FOOTER = "</svg>\n"

# Collect SVG elements
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
def plot_node(node_instance, x, y, local_group):
    """Draw a node as a filled circle with its instance name aligned horizontally."""
    node_name = node_instance.get("instance_name", "")
    cx = x + node_pointsize / 2
    cy = y

    circle = f'<circle cx="{cx}" cy="{cy}" r="{node_pointsize / 2}" fill="white" stroke="black" stroke-width="1"/>'
    label_y = y + node_pointsize + 8
    label = (
        f'<text x="{cx}" y="{label_y}" fill="{FONT_COLOR}" '
        f'text-anchor="middle" font-family="{FONT_FAMILY}" '
        f'font-size="{FONT_SIZE}">{node_name}</text>'
    )
    local_group.append(circle)
    local_group.append(label)


def plot_segment(segment_instance, x, y, length, local_group):
    """Draw a segment as a solid black rectangle (no border)."""
    segment_name = segment_instance.get("instance_name", "")
    rect_height = 2

    rect = f'<rect x="{x}" y="{y - rect_height / 2}" width="{length}" height="{rect_height}" fill="black"/>'
    label_y = y + node_pointsize + 8
    label_x = x + (length / 2)
    label = (
        f'<text x="{label_x}" y="{label_y}" fill="{FONT_COLOR}" '
        f'text-anchor="middle" font-family="{FONT_FAMILY}" '
        f'font-size="{FONT_SIZE}">{segment_name}</text>'
    )
    local_group.append(rect)
    local_group.append(label)


# =============== HEADER ROW ===============
def build_header():
    header_group = []
    y0 = TABLE_MARGIN_Y

    # Column outlines
    header_group.append(
        f'<rect x="{TABLE_MARGIN_X}" y="{y0}" width="{COL1_WIDTH}" height="{HEADER_HEIGHT}" '
        f'fill="{TABLE_FILL}" stroke="{TABLE_STROKE}" />'
    )
    header_group.append(
        f'<rect x="{TABLE_MARGIN_X + COL1_WIDTH}" y="{y0}" width="{COL2_WIDTH}" height="{HEADER_HEIGHT}" '
        f'fill="{TABLE_FILL}" stroke="{TABLE_STROKE}" />'
    )

    # Column labels
    header_group.append(
        f'<text x="{TABLE_MARGIN_X + COL1_WIDTH / 2}" y="{y0 + HEADER_HEIGHT / 2}" '
        f'fill="{FONT_COLOR}" text-anchor="middle" dominant-baseline="middle" '
        f'font-family="{FONT_FAMILY}" font-size="{FONT_SIZE + 1}">Circuit ID</text>'
    )
    header_group.append(
        f'<text x="{TABLE_MARGIN_X + COL1_WIDTH + COL2_WIDTH / 2}" y="{y0 + HEADER_HEIGHT / 2}" '
        f'fill="{FONT_COLOR}" text-anchor="middle" dominant-baseline="middle" '
        f'font-family="{FONT_FAMILY}" font-size="{FONT_SIZE + 1}">Circuit Visualization</text>'
    )
    return header_group


# =============== MAIN LOOP ===============
row_index = 0
y_offset = TABLE_MARGIN_Y + HEADER_HEIGHT

for instance in instances_list.read_instance_rows():
    if instance.get("item_type") != "Circuit":
        continue

    circuit_id = instance.get("circuit_id")
    ports = circuit_instance.instances_of_circuit(circuit_id)

    # Local group for this circuit's graphics
    local_group = []

    # Count nodes and segments
    nodes = [p for p in ports if p.get("location_is_node_or_segment") == "Node"]
    segments = [p for p in ports if p.get("location_is_node_or_segment") == "Segment"]

    num_nodes = len(nodes)
    num_segments = len(segments)

    delta_x = 0
    try:
        segment_length = (
            overall_length - (num_nodes + num_segments) * whitespace_length
        ) / num_segments
    except ZeroDivisionError:
        delta_x = overall_length / num_nodes
        segment_length = 0

    x = 0
    for port in ports:
        item_type = port.get("item_type")
        if item_type == "Connector cavity":
            plot_node(port, x, y=ROW_HEIGHT / 2, local_group=local_group)
            x += whitespace_length + delta_x
        elif item_type == "Conductor":
            plot_segment(
                port,
                x,
                y=ROW_HEIGHT / 2,
                length=segment_length,
                local_group=local_group,
            )
            x += segment_length + whitespace_length

    # Table row outline
    y_row_top = y_offset + (row_index * ROW_HEIGHT)
    svg_elements.append(
        f'<rect x="{TABLE_MARGIN_X}" y="{y_row_top}" width="{COL1_WIDTH}" height="{ROW_HEIGHT}" '
        f'fill="{TABLE_FILL}" stroke="{TABLE_STROKE}" />'
    )
    svg_elements.append(
        f'<rect x="{TABLE_MARGIN_X + COL1_WIDTH}" y="{y_row_top}" width="{COL2_WIDTH}" height="{ROW_HEIGHT}" '
        f'fill="{TABLE_FILL}" stroke="{TABLE_STROKE}" />'
    )

    # Left cell text (Circuit ID)
    svg_elements.append(
        f'<text x="{TABLE_MARGIN_X + COL1_WIDTH / 2}" y="{y_row_top + ROW_HEIGHT / 2}" '
        f'fill="{FONT_COLOR}" text-anchor="middle" dominant-baseline="middle" '
        f'font-family="{FONT_FAMILY}" font-size="{FONT_SIZE}">{circuit_id}</text>'
    )

    # Right cell (graphics group)
    group_x = TABLE_MARGIN_X + COL1_WIDTH + VISUALIZATION_INSET_X
    group_y = y_row_top
    svg_elements.append(f'<g transform="translate({group_x},{group_y})">')
    for element in local_group:
        svg_elements.append(f"  {element}")
    svg_elements.append("</g>")

    row_index += 1


# =============== WRITE SVG ===============
output_path = path("circuit visualizer svg")
os.makedirs(os.path.dirname(output_path), exist_ok=True)

with open(output_path, "w", encoding="utf-8") as f:
    f.write(SVG_HEADER)
    f.write(f'<g id="{artifact_id}-circuit-visualizer-contents-start">\n')

    # Header row
    for h in build_header():
        f.write(f"  {h}\n")

    # Table rows
    for element in svg_elements:
        f.write(f"  {element}\n")

    f.write("</g>\n")
    f.write(f'<g id="{artifact_id}-circuit-visualizer-contents-end"/>\n')
    f.write(SVG_FOOTER)

print(f"SVG written to: {output_path}")
