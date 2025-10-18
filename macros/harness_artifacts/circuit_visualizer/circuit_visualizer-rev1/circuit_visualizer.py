import os
from harnice import fileio, instances_list, circuit_instance

artifact_mpn = "circuit_visualizer"

# =============== GLOBAL SETTINGS ===============
node_pointsize = 6
overall_length = 480
whitespace_length = 24

# Font and style
FONT_FAMILY = "Arial"
FONT_SIZE = 7
FONT_COLOR = "black"

# Table layout
HEADER_HEIGHT = 16
ROW_HEIGHT = 30
outer_margin_length = 96  # ~1 inch margin from table edges to first/last node
COL1_WIDTH = 72
TABLE_MARGIN_X = 16
TABLE_MARGIN_Y = 16
TABLE_STROKE = "black"
TABLE_FILL = "white"

# Derived layout
COL2_WIDTH = (
    overall_length + 2 * whitespace_length
)  # right cell width = visualization + margin
VISUALIZATION_INSET_X = whitespace_length  # left inset centers visualization

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
def plot_node(node_instance, x, y, local_group, text_position):
    """Draw a node as a filled circle with its instance name positioned relative to it."""
    print_name = node_instance.get("print_name", "")
    cx = x + node_pointsize / 2
    cy = y

    circle = (
        f'<circle cx="{cx}" cy="{cy}" r="{node_pointsize / 2}" '
        f'fill="white" stroke="black" stroke-width="1"/>'
    )

    # Default offsets
    offset = 8
    label_x = cx
    label_y = cy
    text_anchor = "middle"
    dominant_baseline = "middle"

    if text_position == "above":
        label_y = cy - offset
        text_anchor = "middle"
        dominant_baseline = "auto"
    elif text_position == "below":
        label_y = cy + offset
        text_anchor = "middle"
        dominant_baseline = "hanging"
    elif text_position == "left":
        label_x = cx - offset
        text_anchor = "end"
        dominant_baseline = "middle"
    elif text_position == "right":
        label_x = cx + offset
        text_anchor = "start"
        dominant_baseline = "middle"
    else:
        label_y = cy + offset
        text_anchor = "middle"
        dominant_baseline = "hanging"

    label = (
        f'<text x="{label_x}" y="{label_y}" fill="{FONT_COLOR}" '
        f'text-anchor="{text_anchor}" dominant-baseline="{dominant_baseline}" '
        f'font-family="{FONT_FAMILY}" font-size="{FONT_SIZE}">{print_name}</text>'
    )

    local_group.append(circle)
    local_group.append(label)


def plot_segment(segment_instance, x, y, length, local_group):
    """Draw a segment as a solid black rectangle (no border),
    with the segment label centered on the line over a white background.
    """
    print_name = segment_instance.get("print_name", "")
    rect_height = 2

    # Black line
    rect = f'<rect x="{x}" y="{y - rect_height / 2}" width="{length}" height="{rect_height}" fill="black"/>'

    # Label position
    label_y = y + FONT_SIZE / 2 - 1  # vertically centered slightly above midline
    label_x = x + (length / 2)

    # Measure background box around text
    text_padding_x = 3
    text_padding_y = 2
    approx_text_width = len(print_name) * (FONT_SIZE * 0.6)
    bg_x = label_x - (approx_text_width / 2) - text_padding_x
    bg_y = label_y - FONT_SIZE + text_padding_y / 2

    # White rectangle under text (no border)
    label_bg = (
        f'<rect x="{bg_x}" y="{bg_y}" '
        f'width="{approx_text_width + 2 * text_padding_x}" '
        f'height="{FONT_SIZE + text_padding_y}" fill="white"/>'
    )

    # Label text
    label = (
        f'<text x="{label_x}" y="{label_y}" fill="{FONT_COLOR}" '
        f'text-anchor="middle" font-family="{FONT_FAMILY}" '
        f'font-size="{FONT_SIZE}">{print_name}</text>'
    )

    # Append elements (order: line → bg → text)
    local_group.append(rect)
    local_group.append(label_bg)
    local_group.append(label)


# =============== HEADER ROW ===============
def build_header():
    header_group = []
    y0 = TABLE_MARGIN_Y

    # Column outlines (gray fill for header)
    header_group.append(
        f'<rect x="{TABLE_MARGIN_X}" y="{y0}" width="{COL1_WIDTH}" height="{HEADER_HEIGHT}" '
        f'fill="#E0E0E0" stroke="{TABLE_STROKE}" />'
    )
    header_group.append(
        f'<rect x="{TABLE_MARGIN_X + COL1_WIDTH}" y="{y0}" width="{COL2_WIDTH}" height="{HEADER_HEIGHT}" '
        f'fill="#E0E0E0" stroke="{TABLE_STROKE}" />'
    )

    # Column labels (bold)
    header_group.append(
        f'<text x="{TABLE_MARGIN_X + COL1_WIDTH / 2}" y="{y0 + HEADER_HEIGHT / 2}" '
        f'fill="{FONT_COLOR}" text-anchor="middle" dominant-baseline="middle" '
        f'font-family="{FONT_FAMILY}" font-size="{FONT_SIZE + 1}" font-weight="bold">CIRCUIT</text>'
    )
    header_group.append(
        f'<text x="{TABLE_MARGIN_X + COL1_WIDTH + COL2_WIDTH / 2}" y="{y0 + HEADER_HEIGHT / 2}" '
        f'fill="{FONT_COLOR}" text-anchor="middle" dominant-baseline="middle" '
        f'font-family="{FONT_FAMILY}" font-size="{FONT_SIZE + 1}" font-weight="bold">SCHEMATIC</text>'
    )
    return header_group


# =============== MAIN LOOP ===============
row_index = 0
y_offset = TABLE_MARGIN_Y + HEADER_HEIGHT

for instance in instances_list.read_instance_rows():
    if instance.get("item_type") != "Circuit":
        continue

    circuit_id = instance.get("circuit_id")
    print_name = instance.get("print_name", "")
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
            overall_length
            - (2 * outer_margin_length)  # reserve left/right margins
            - (num_nodes + num_segments - 1) * whitespace_length
        ) / num_segments
    except ZeroDivisionError:
        delta_x = (overall_length - 2 * outer_margin_length) / max(num_nodes, 1)
        segment_length = 0

    x = outer_margin_length  # start after left margin
    for i, port in enumerate(ports):
        kind = port.get("location_is_node_or_segment")

        if kind == "Node":
            circuit_port_number = int(port.get("circuit_port_number") or -1)
            num_ports = len(ports) - 1  # zero-based last index

            # --- Determine label position ---
            if circuit_port_number == 0:
                text_position = "left"
            elif circuit_port_number == num_ports:
                text_position = "right"
            else:
                prev_port = ports[i - 1] if i > 0 else None
                if prev_port:
                    if prev_port.get("location_is_node_or_segment") == "Node":
                        prev_text_pos = prev_port.get("text_position", "below")
                        text_position = "above" if prev_text_pos == "below" else "below"
                    elif prev_port.get("location_is_node_or_segment") == "Segment":
                        text_position = "above"
                    else:
                        text_position = "below"
                else:
                    text_position = "below"

            port["text_position"] = text_position

            # --- Draw node ---
            plot_node(
                node_instance=port,
                x=x,
                y=ROW_HEIGHT / 2,
                local_group=local_group,
                text_position=text_position,
            )

            # --- Determine what comes next ---
            next_item = ports[i + 1] if i + 1 < len(ports) else None
            if next_item:
                if next_item.get("location_is_node_or_segment") == "Segment":
                    # Draw the segment immediately after this node
                    plot_segment(
                        segment_instance=next_item,
                        x=x + node_pointsize,
                        y=ROW_HEIGHT / 2,
                        length=segment_length,
                        local_group=local_group,
                    )
                    # Move to the end of the segment for the next element
                    x += node_pointsize + segment_length
                elif next_item.get("location_is_node_or_segment") == "Node":
                    # Only add whitespace if next is another node
                    x += whitespace_length

        elif kind == "Segment":
            # Segments are now handled inline after their preceding Node
            continue

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
        f'font-family="{FONT_FAMILY}" font-size="{FONT_SIZE}">{print_name}</text>'
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
