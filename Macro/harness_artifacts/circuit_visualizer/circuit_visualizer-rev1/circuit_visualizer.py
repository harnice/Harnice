import os
from harnice import fileio, state
from harnice.lists import instances_list
from harnice.utils import circuit_utils, appearance, svg_utils

artifact_mpn = "circuit_visualizer"

# =============== PATHS ===================================================================================
def macro_file_structure():
    return {
        f"{state.partnumber('pn-rev')}-{artifact_id}-circuit-visualizer-master.svg": "circuit visualizer svg",
    }

if base_directory is None:  # path between cwd and the file structure for this macro
    base_directory = os.path.join("instance_data", "macro", artifact_id)

def path(target_value):
    return fileio.path(target_value, structure_dict=macro_file_structure(), base_directory=base_directory)

def dirpath(target_value):
    # target_value = None will return the root of this macro
    return fileio.dirpath(target_value, structure_dict=macro_file_structure(), base_directory=base_directory)
# ==========================================================================================================


# =============== GLOBAL SETTINGS ===============
node_pointsize = 6
circuit_length = 480
whitespace_length = 24

# Font and style
FONT_FAMILY = "Arial"
FONT_SIZE = 7
FONT_COLOR = "black"
line_spacing = 7

# Table layout
HEADER_HEIGHT = 16
ROW_HEIGHT = 30
COL1_WIDTH = 72
TABLE_STROKE = "black"
TABLE_FILL = "white"

# node box margins (apply globally)
NODE_MARGIN_X = 5
NODE_MARGIN_Y = 3

# Derived layout
COL2_WIDTH = circuit_length + 2 * whitespace_length
VISUALIZATION_INSET_X = whitespace_length

# SVG header/footer
SVG_HEADER = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg xmlns="http://www.w3.org/2000/svg" version="1.1">
"""
SVG_FOOTER = "</svg>\n"

svg_elements = []


# =============== FUNCTIONS ===============
def plot_node(node_instance, x, y, box_width, local_group):
    """Draw a rectangular node box of fixed width centered vertically in its row."""
    # Text lines
    line1 = node_instance.get("item_type", "")
    line2 = instances_list.attribute_of(node_instance.get("parent_instance"), "print_name")
    line3 = node_instance.get("print_name", "")
    lines = [line1, line2, line3]

    # Geometry
    box_height = ROW_HEIGHT - (2 * NODE_MARGIN_Y)
    box_y = y - (box_height / 2)
    rect = (
        f'<rect x="{x}" y="{box_y}" width="{box_width}" height="{box_height}" '
        f'fill="white" stroke="black" stroke-width="1"/>'
    )
    local_group.append(rect)

    # Text
    text_x = x + (box_width / 2)
    total_text_height = len(lines) * line_spacing
    start_y = y - (total_text_height / 2) + (FONT_SIZE / 2)
    text_template = (
        f'<text x="{{x}}" y="{{y}}" fill="{FONT_COLOR}" '
        f'text-anchor="middle" font-family="{FONT_FAMILY}" '
        f'font-size="{FONT_SIZE}">{{text}}</text>'
    )
    for i, text in enumerate(lines):
        ty = start_y + i * line_spacing
        local_group.append(text_template.format(x=text_x, y=ty, text=text))

    return box_width


def plot_segment(segment_instance, x, y, length, local_group):
    appearance_dict = appearance.parse(segment_instance.get("appearance", "{}"))
    stroke_width = 4

    # If svg_utils flips Y internally, counteract that here by negating y.
    y_for_path = -y

    spline_points = [
        {"x": x,           "y": y_for_path, "tangent": 0},
        {"x": x + length,  "y": y_for_path, "tangent": 0},
    ]
    svg_utils.draw_styled_path(spline_points, stroke_width, appearance_dict, local_group)

    # Labels (normal SVG Y, don't negate)
    line1 = instances_list.attribute_of(segment_instance.get("instance_name"), "parent_instance")
    line2 = segment_instance.get("print_name")
    label_x = x + (length / 2)
    label_y_center = y
    line1_y = label_y_center - (line_spacing / 2)
    line2_y = label_y_center + (line_spacing / 2)

    text_padding_x = 3
    text_padding_y = 2
    try:
        text_width = max(len(line1), len(line2)) * (FONT_SIZE * 0.6)
    except TypeError:
        text_width = 0
    text_height = FONT_SIZE * 2 + line_spacing + text_padding_y
    bg_x = label_x - (text_width / 2) - text_padding_x
    bg_y = label_y_center - (text_height / 2)

    local_group.append(
        f'<rect x="{bg_x}" y="{bg_y}" width="{text_width + 2 * text_padding_x}" '
        f'height="{text_height}" fill="white" />'
    )

    text_template = (
        f'<text x="{{x}}" y="{{y}}" fill="{FONT_COLOR}" '
        f'text-anchor="middle" font-family="{FONT_FAMILY}" '
        f'font-size="{FONT_SIZE}">{{text}}</text>'
    )
    local_group.append(text_template.format(x=label_x, y=line1_y, text=line1))
    local_group.append(text_template.format(x=label_x, y=line2_y, text=line2))


# =============== HEADER ROW ===============
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


# =============== MAIN ===============
row_index = 0
y_offset = HEADER_HEIGHT

for instance in fileio.read_tsv("instances list"):
    if instance.get("item_type") != "circuit":
        continue

    circuit_id = instance.get("circuit_id")
    print_name = instance.get("print_name", "")
    ports = circuit_utils.instances_of_circuit(circuit_id)
    local_group = []

    # Collect node/segment data
    nodes = [p for p in ports if p.get("location_type") == "node"]
    segments = [p for p in ports if p.get("location_type") == "segment"]
    num_nodes = len(nodes)
    num_segments = len(segments)

    # Compute uniform node width
    max_text_width = 0
    for node in nodes:
        line1 = node.get("item_type", "")
        line2 = instances_list.attribute_of(node.get("parent_instance"), "print_name")
        line3 = node.get("print_name", "")
        text_width = max(len(t) for t in [line1, line2, line3]) * (FONT_SIZE * 0.6)
        max_text_width = max(max_text_width, text_width)
    uniform_node_width = max_text_width + 16

    # Compute segment lengths
    usable_width = COL2_WIDTH - (2 * NODE_MARGIN_X)
    total_node_width = num_nodes * uniform_node_width
    remaining_space = usable_width - total_node_width
    segment_length = remaining_space / max(num_segments, 1) if num_segments else 0
    segment_length = max(segment_length, 0)

    # Draw schematic contents
    x = NODE_MARGIN_X
    for port in ports:
        if port.get("location_type") == "node":
            plot_node(port, x, ROW_HEIGHT / 2, uniform_node_width, local_group)
            x += uniform_node_width
        elif port.get("location_type") == "segment":
            plot_segment(port, x, ROW_HEIGHT / 2, segment_length, local_group)
            x += segment_length

    # Draw cell outlines
    y_row_top = y_offset + (row_index * ROW_HEIGHT)
    svg_elements.append(
        f'<rect x="0" y="{y_row_top}" width="{COL1_WIDTH}" height="{ROW_HEIGHT}" '
        f'fill="{TABLE_FILL}" stroke="{TABLE_STROKE}" />'
    )
    svg_elements.append(
        f'<rect x="{COL1_WIDTH}" y="{y_row_top}" width="{COL2_WIDTH}" height="{ROW_HEIGHT}" '
        f'fill="{TABLE_FILL}" stroke="{TABLE_STROKE}" />'
    )

    # Left cell label
    svg_elements.append(
        f'<text x="{COL1_WIDTH / 2}" y="{y_row_top + ROW_HEIGHT / 2}" '
        f'fill="{FONT_COLOR}" text-anchor="middle" dominant-baseline="middle" '
        f'font-family="{FONT_FAMILY}" font-size="{FONT_SIZE}">{print_name}</text>'
    )

    # Content group
    group_x = COL1_WIDTH
    group_y = y_row_top
    svg_elements.append(f'<g transform="translate({group_x},{group_y})">')
    for element in local_group:
        svg_elements.append(f"  {element}")
    svg_elements.append("</g>")

    row_index += 1


# =============== WRITE SVG ===============
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
