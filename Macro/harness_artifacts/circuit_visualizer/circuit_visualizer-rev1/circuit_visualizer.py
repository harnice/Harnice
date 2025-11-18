import os
from harnice import fileio, state
from harnice.lists import instances_list
from harnice.utils import circuit_utils, appearance, svg_utils

artifact_mpn = "circuit_visualizer"
# artifact_id: intentionally NOT defined here — injected externally by runpy


# ==========================================================================================================
# PATHS
# ==========================================================================================================

def macro_file_structure():
    return {
        f"{state.partnumber('pn-rev')}-{artifact_id}-circuit-visualizer-master.svg": "circuit visualizer svg",
    }


if base_directory is None:  # path between cwd and this macro's file structure
    base_directory = os.path.join("instance_data", "macro", artifact_id)


def path(target_value):
    return fileio.path(
        target_value,
        structure_dict=macro_file_structure(),
        base_directory=base_directory,
    )


def dirpath(target_value):
    return fileio.dirpath(
        target_value,
        structure_dict=macro_file_structure(),
        base_directory=base_directory,
    )


# ==========================================================================================================
# GLOBAL SETTINGS
# ==========================================================================================================

node_pointsize = 6
circuit_length = 600
whitespace_length = 24

FONT_FAMILY = "Arial"
FONT_SIZE = 7
FONT_COLOR = "black"
line_spacing = 7

HEADER_HEIGHT = 16
ROW_HEIGHT = 30
COL1_WIDTH = 72
TABLE_STROKE = "black"
TABLE_FILL = "white"

NODE_MARGIN_X = 5
NODE_MARGIN_Y = 3
NODE_WIDTH = 84

COL2_WIDTH = circuit_length + 2 * whitespace_length
VISUALIZATION_INSET_X = whitespace_length

SVG_HEADER = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg xmlns="http://www.w3.org/2000/svg" version="1.1">
"""
SVG_FOOTER = "</svg>\n"

svg_elements = []


# ==========================================================================================================
# UTILITY: CONSOLIDATED TEXT RENDERING
# ==========================================================================================================

def plot_text_lines(lines, center_x, center_y, text_group):
    """Draw 1–3 centered text lines at a given row-relative location."""
    total_text_height = len(lines) * line_spacing
    start_y = center_y - (total_text_height / 2) + (FONT_SIZE / 2)

    text_template = (
        f'<text x="{{x}}" y="{{y}}" fill="{FONT_COLOR}" '
        f'text-anchor="middle" font-family="{FONT_FAMILY}" '
        f'font-size="{FONT_SIZE}">{{text}}</text>'
    )

    for i, text in enumerate(lines):
        ty = start_y + i * line_spacing
        text_group.append(
            text_template.format(x=center_x, y=ty, text=text)
        )


# ==========================================================================================================
# NODE + SEGMENT SHAPES (NO TEXT HERE)
# ==========================================================================================================

def plot_node_shape(node_instance, x, y, box_width, node_group):
    """Draw only the rectangular node box."""
    box_height = ROW_HEIGHT - (2 * NODE_MARGIN_Y)
    box_y = y - (box_height / 2)

    rect = (
        f'<rect x="{x}" y="{box_y}" width="{box_width}" height="{box_height}" '
        f'fill="white" stroke="black" stroke-width="1"/>'
    )
    node_group.append(rect)


def plot_segment_shape(segment_instance, x, y, length, segment_group):
    """
    Draw the styled spline path for a segment.
    Returns (center_x, center_y) for text placement.
    """
    y_for_path = -y  # svg_utils flips Y internally

    spline_points = [
        {"x": x, "y": y_for_path, "tangent": 0},
        {"x": x + length, "y": y_for_path, "tangent": 0},
    ]
    svg_utils.draw_styled_path(
        spline_points, 0.02, segment_instance.get("appearance"), segment_group
    )

    return x + (length / 2), y


# ==========================================================================================================
# HEADER
# ==========================================================================================================

def build_header():
    header_group = []
    y0 = 0

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


# ==========================================================================================================
# MAIN RENDER LOOP
# ==========================================================================================================
row_index = 0
y_offset = HEADER_HEIGHT

for instance in fileio.read_tsv("instances list"):
    if instance.get("item_type") != "circuit":
        continue

    circuit_id = instance.get("circuit_id")
    print_name = instance.get("print_name")
    ports_unfiltered = circuit_utils.instances_of_circuit(circuit_id)
    ports = []
    for port in ports_unfiltered:
        if "-segment" not in port.get("item_type"):
            ports.append(port)

    nodes = []
    for p in ports:
        if p.get("location_type") == "node":
            nodes.append(p)

    segments = []
    for p in ports:
        if p.get("location_type") == "segment":
            continue
        segments.append(p)

    usable_width = COL2_WIDTH - (2 * NODE_MARGIN_X)
    total_node_width = len(nodes) * NODE_WIDTH
    remaining_space = usable_width - total_node_width
    segment_length = (remaining_space / max(len(segments), 1)) if segments else 0
    segment_length = max(segment_length, 0)

    # ---- SVG row groups ----
    y_row_top = y_offset + (row_index * ROW_HEIGHT)
    group_x = COL1_WIDTH
    group_y = y_row_top

    table_group = []
    segment_group = []
    node_group = []
    text_group = []

    # ---- Table cell backgrounds ----
    table_group.append(
        f'<rect x="0" y="{y_row_top}" width="{COL1_WIDTH}" height="{ROW_HEIGHT}" '
        f'fill="{TABLE_FILL}" stroke="{TABLE_STROKE}" />'
    )
    table_group.append(
        f'<rect x="{COL1_WIDTH}" y="{y_row_top}" width="{COL2_WIDTH}" height="{ROW_HEIGHT}" '
        f'fill="{TABLE_FILL}" stroke="{TABLE_STROKE}" />'
    )

    # ---- Row label ----
    text_group.append(
        f'<text x="{COL1_WIDTH / 2}" y="{y_row_top + ROW_HEIGHT / 2}" '
        f'fill="{FONT_COLOR}" text-anchor="middle" dominant-baseline="middle" '
        f'font-family="{FONT_FAMILY}" font-size="{FONT_SIZE}">{print_name}</text>'
    )

    # ---- Draw schematic content ----
    x = NODE_MARGIN_X
    row_center_y = ROW_HEIGHT / 2

    for port in ports:
        if port.get("location_type") == "segment":

            cx, cy = plot_segment_shape(port, x, row_center_y, segment_length, segment_group)

            lines = [
                instances_list.attribute_of(port.get("parent_instance"), "print_name"),
                port.get("print_name")
            ]
            plot_text_lines(lines, group_x + cx, group_y + cy, text_group)

            x += segment_length

        elif port.get("location_type") == "node":
            box_width = NODE_WIDTH
            plot_node_shape(port, x, row_center_y, box_width, node_group)

            lines = [
                port.get("item_type", ""),
                instances_list.attribute_of(port.get("parent_instance"), "print_name"),
                port.get("print_name", "")
            ]

            cx = x + (box_width / 2)
            cy = row_center_y

            plot_text_lines(lines, group_x + cx, group_y + cy, text_group)

            x += box_width

    # ---- Output row groups ----
    svg_elements.extend(table_group)
    svg_elements.append(f'<g transform="translate({group_x},{group_y})">')
    for s in segment_group:
        svg_elements.append(f"  {s}")
    for n in node_group:
        svg_elements.append(f"  {n}")
    svg_elements.append("</g>")
    svg_elements.extend(text_group)

    row_index += 1


# ==========================================================================================================
# WRITE SVG
# ==========================================================================================================

with open(path("circuit visualizer svg"), "w", encoding="utf-8") as f:
    f.write(SVG_HEADER)
    f.write(f'<g id="{artifact_id}-circuit-visualizer-contents-start">\n')

    for h in build_header():
        f.write(f"  {h}\n")

    for element in svg_elements:
        f.write(f"  {element}\n")

    f.write("</g>\n")
    f.write(f'<g id="{artifact_id}-circuit-visualizer-contents-end"/>\n')
    f.write(SVG_FOOTER)
