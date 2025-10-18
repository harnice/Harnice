import os
from harnice import fileio, instances_list, circuit_instance

artifact_mpn = "circuit_visualizer"

# =============== GLOBAL SETTINGS ===============
node_pointsize = 6
circuit_length = 480
whitespace_length = 24

# Font and style
FONT_FAMILY = "Arial"
FONT_SIZE = 7
FONT_COLOR = "black"

# Table layout
HEADER_HEIGHT = 16
ROW_HEIGHT = 30
margin_btwn_circuit_and_table_cell = 96  # ~1 inch margin from table cell edge to first/last node
COL1_WIDTH = 72
TABLE_STROKE = "black"
TABLE_FILL = "white"

# Derived layout
COL2_WIDTH = (
    circuit_length + 2 * whitespace_length
)  # right cell width = visualization + margin
VISUALIZATION_INSET_X = whitespace_length  # left inset inside right cell

# SVG header/footer
SVG_HEADER = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg xmlns="http://www.w3.org/2000/svg" version="1.1">
"""
SVG_FOOTER = "</svg>\n"

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
    """Draw a node circle and its label."""
    print_name = node_instance.get("print_name", "")
    cx = x + node_pointsize / 2
    cy = y

    circle = (
        f'<circle cx="{cx}" cy="{cy}" r="{node_pointsize / 2}" '
        f'fill="white" stroke="black" stroke-width="1"/>'
    )

    offset = 8
    label_x = cx
    label_y = cy
    text_anchor = "middle"
    dominant_baseline = "middle"

    if text_position == "above":
        label_y = cy - offset
        dominant_baseline = "auto"
    elif text_position == "below":
        label_y = cy + offset
        dominant_baseline = "hanging"
    elif text_position == "left":
        label_x = cx - offset
        text_anchor = "end"
    elif text_position == "right":
        label_x = cx + offset
        text_anchor = "start"

    label = (
        f'<text x="{label_x}" y="{label_y}" fill="{FONT_COLOR}" '
        f'text-anchor="{text_anchor}" dominant-baseline="{dominant_baseline}" '
        f'font-family="{FONT_FAMILY}" font-size="{FONT_SIZE}">{print_name}</text>'
    )

    local_group.append(circle)
    local_group.append(label)


def plot_segment(segment_instance, x, y, length, local_group):
    """Draw a segment as a solid black rectangle with centered text and white background."""
    print_name = segment_instance.get("print_name", "")
    rect_height = 2

    rect = f'<rect x="{x}" y="{y - rect_height / 2}" width="{length}" height="{rect_height}" fill="black"/>'

    label_y = y + FONT_SIZE / 2 - 1
    label_x = x + (length / 2)

    text_padding_x = 3
    text_padding_y = 2
    approx_text_width = len(print_name) * (FONT_SIZE * 0.6)
    bg_x = label_x - (approx_text_width / 2) - text_padding_x
    bg_y = label_y - FONT_SIZE + text_padding_y / 2

    label_bg = (
        f'<rect x="{bg_x}" y="{bg_y}" '
        f'width="{approx_text_width + 2 * text_padding_x}" '
        f'height="{FONT_SIZE + text_padding_y}" fill="white"/>'
    )

    label = (
        f'<text x="{label_x}" y="{label_y}" fill="{FONT_COLOR}" '
        f'text-anchor="middle" font-family="{FONT_FAMILY}" '
        f'font-size="{FONT_SIZE}">{print_name}</text>'
    )

    local_group.append(rect)
    local_group.append(label_bg)
    local_group.append(label)


# =============== HEADER ROW ===============
def build_header():
    header_group = []
    y0 = 0  # header starts at top of SVG

    header_group.append(
        f'<rect x="0" y="{y0}" width="{COL1_WIDTH}" height="{HEADER_HEIGHT}" '
        f'fill="#E0E0E0" stroke="{TABLE_STROKE}" />'
    )
    header_group.append(
        f'<rect x="{COL1_WIDTH}" y="{y0}" width="{COL2_WIDTH}" height="{HEADER_HEIGHT}" '
        f'fill="#E0E0E0" stroke="{TABLE_STROKE}" />'
    )

    header_group.append(
        f'<text x="{COL1_WIDTH / 2}" y="{y0 + HEADER_HEIGHT / 2}" '
        f'fill="{FONT_COLOR}" text-anchor="middle" dominant-baseline="middle" '
        f'font-family="{FONT_FAMILY}" font-size="{FONT_SIZE + 1}" font-weight="bold">CIRCUIT</text>'
    )
    header_group.append(
        f'<text x="{COL1_WIDTH + COL2_WIDTH / 2}" y="{y0 + HEADER_HEIGHT / 2}" '
        f'fill="{FONT_COLOR}" text-anchor="middle" dominant-baseline="middle" '
        f'font-family="{FONT_FAMILY}" font-size="{FONT_SIZE + 1}" font-weight="bold">SCHEMATIC</text>'
    )
    return header_group


# =============== MAIN LOOP ===============
row_index = 0
y_offset = HEADER_HEIGHT  # rows begin immediately below header

for instance in instances_list.read_instance_rows():
    if instance.get("item_type") != "Circuit":
        continue

    circuit_id = instance.get("circuit_id")
    print_name = instance.get("print_name", "")
    ports = circuit_instance.instances_of_circuit(circuit_id)

    local_group = []

    nodes = [p for p in ports if p.get("location_is_node_or_segment") == "Node"]
    segments = [p for p in ports if p.get("location_is_node_or_segment") == "Segment"]

    num_nodes = len(nodes)
    num_segments = len(segments)

    try:
        segment_length = (
            circuit_length
            - (2 * margin_btwn_circuit_and_table_cell)
            - (num_nodes + num_segments - 1) * whitespace_length
        ) / num_segments
    except ZeroDivisionError:
        segment_length = 0

    x = margin_btwn_circuit_and_table_cell
    for i, port in enumerate(ports):
        if port.get("item_type") == "Multi-Circuit Port":
            raise NotImplementedError("Multi-Circuit Ports are not supported yet")
        
        kind = port.get("location_is_node_or_segment")

        if kind == "Node":
            circuit_port_number = int(port.get("circuit_port_number") or -1)
            num_ports = len(ports) - 1

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
                    else:
                        text_position = "above"
                else:
                    text_position = "below"

            port["text_position"] = text_position

            plot_node(
                node_instance=port,
                x=x,
                y=ROW_HEIGHT / 2,
                local_group=local_group,
                text_position=text_position,
            )

            next_item = ports[i + 1] if i + 1 < len(ports) else None
            if next_item:
                if next_item.get("location_is_node_or_segment") == "Segment":
                    plot_segment(
                        segment_instance=next_item,
                        x=x + node_pointsize,
                        y=ROW_HEIGHT / 2,
                        length=segment_length,
                        local_group=local_group,
                    )
                    x += node_pointsize + segment_length
                elif next_item.get("location_is_node_or_segment") == "Node":
                    x += whitespace_length

    y_row_top = y_offset + (row_index * ROW_HEIGHT)
    svg_elements.append(
        f'<rect x="0" y="{y_row_top}" width="{COL1_WIDTH}" height="{ROW_HEIGHT}" '
        f'fill="{TABLE_FILL}" stroke="{TABLE_STROKE}" />'
    )
    svg_elements.append(
        f'<rect x="{COL1_WIDTH}" y="{y_row_top}" width="{COL2_WIDTH}" height="{ROW_HEIGHT}" '
        f'fill="{TABLE_FILL}" stroke="{TABLE_STROKE}" />'
    )

    svg_elements.append(
        f'<text x="{COL1_WIDTH / 2}" y="{y_row_top + ROW_HEIGHT / 2}" '
        f'fill="{FONT_COLOR}" text-anchor="middle" dominant-baseline="middle" '
        f'font-family="{FONT_FAMILY}" font-size="{FONT_SIZE}">{print_name}</text>'
    )

    group_x = COL1_WIDTH + VISUALIZATION_INSET_X
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

    for h in build_header():
        f.write(f"  {h}\n")

    for element in svg_elements:
        f.write(f"  {element}\n")

    f.write("</g>\n")
    f.write(f'<g id="{artifact_id}-circuit-visualizer-contents-end"/>\n')
    f.write(SVG_FOOTER)

print(f"SVG written to: {output_path}")
