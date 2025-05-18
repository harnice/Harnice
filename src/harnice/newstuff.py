import os
import json
import xml.etree.ElementTree as ET
from harnice import (
    harnice_prechecker
)

def part(
    library,
    mfgmpn
    ):

    global pn, rev
    pn = harnice_prechecker.pn_from_cwd()
    rev = harnice_prechecker.rev_from_cwd()

    if(harnice_prechecker.harnice_prechecker() == False):
        return

    #======== MAKE NEW PART JSON ===========
    attributes_blank_json = {
        "plotting_info": {
            "csys_parent_prefs": [
                ".node"
            ],
            "component_translate_inches": {
                "translate_x": 0,
                "translate_y": 0,
                "rotate_csys": 0
            }
        },
        "tooling_info": {
            "tools": []
        },
        "build_notes": [],
        "flagnote_locations": [
            {"angle": 0, "distance": 2, "arrowhead_angle": "", "arrowhead_distance": 1},
            {"angle": 15, "distance": 2, "arrowhead_angle": "", "arrowhead_distance": 1},
            {"angle": -15, "distance": 2, "arrowhead_angle": "", "arrowhead_distance": 1},
            {"angle": 30, "distance": 2, "arrowhead_angle": "", "arrowhead_distance": 1},
            {"angle": -30, "distance": 2, "arrowhead_angle": "", "arrowhead_distance": 1},
            {"angle": 45, "distance": 2, "arrowhead_angle": "", "arrowhead_distance": 1},
            {"angle": -45, "distance": 2, "arrowhead_angle": "", "arrowhead_distance": 1},
            {"angle": 60, "distance": 2, "arrowhead_angle": "", "arrowhead_distance": 1},
            {"angle": -60, "distance": 2, "arrowhead_angle": "", "arrowhead_distance": 1},
            {"angle": -75, "distance": 2, "arrowhead_angle": "", "arrowhead_distance": 1},
            {"angle": 75, "distance": 2, "arrowhead_angle": "", "arrowhead_distance": 1},
            {"angle": -90, "distance": 2, "arrowhead_angle": "", "arrowhead_distance": 1},
            {"angle": 90, "distance": 2, "arrowhead_angle": "", "arrowhead_distance": 1},
            {"angle": -105, "distance": 2, "arrowhead_angle": "", "arrowhead_distance": 1},
            {"angle": 105, "distance": 2, "arrowhead_angle": "", "arrowhead_distance": 1},
            {"angle": -120, "distance": 2, "arrowhead_angle": "", "arrowhead_distance": 1},
        ]
    }

    attributes_blank_json_path = os.path.join(os.getcwd(), f"{pn}-attributes.json")

    if os.path.exists(attributes_blank_json_path):
        os.remove(attributes_blank_json_path)

    # Write new file
    with open(attributes_blank_json_path, "w") as json_file:
        json.dump(attributes_blank_json, json_file, indent=4)

# Function to create the root SVG element
#def make_new_part_svg():
    #add_defs()
    #add_named_view()
    #add_content()
    #save_svg()

    width=500
    height=500
    svg = ET.Element("svg", {
        "version": "1.1",
        "id": "svg1",
        "xmlns": "http://www.w3.org/2000/svg",
        "xmlns:svg": "http://www.w3.org/2000/svg",
        "xmlns:inkscape": "http://www.inkscape.org/namespaces/inkscape",
        "xmlns:sodipodi": "http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd"
    })

    #add a defs section with a rectangle and marker
    defs = ET.SubElement(svg, "defs", {"id": "defs1"})

    # Add rectangle
    ET.SubElement(defs, "rect", {
        "x": "197.53245",
        "y": "17.037839",
        "width": "138.96487",
        "height": "107.55136",
        "id": "rect1"
    })

    # Add marker
    marker = ET.SubElement(defs, "marker", {
        "style": "overflow:visible",
        "id": "ConcaveTriangle-80",
        "refX": "0",
        "refY": "0",
        "orient": "auto-start-reverse",
        "markerWidth": "1",
        "markerHeight": "1",
        "viewBox": "0 0 1 1"
    })
    ET.SubElement(marker, "path", {
        "transform": "scale(0.7)",
        "d": "M -2,-4 9,0 -2,4 c 2,-2.33 2,-5.66 0,-8 z",
        "style": "fill:context-stroke;fill-rule:evenodd;stroke:none",
        "id": "path7-4"
    })

    #add a named view
    ET.SubElement(svg, "sodipodi:namedview", {
        "id": "namedview1",
        "pagecolor": "#ffffff",
        "bordercolor": "#000000",
        "borderopacity": "0.25",
        "inkscape:showpageshadow": "2",
        "inkscape:pageopacity": "0.0",
        "inkscape:deskcolor": "#d1d1d1",
    })

    #add content groups with parametrized buildnotes
    contents = ET.SubElement(svg, "g", {"id": "connector-drawing-contents-start"})

    drawing_group = ET.SubElement(contents, "g", {"id": "connector-drawing"})
    add_drawing = ET.SubElement(drawing_group, "g", {"id": "add-drawing-here"})

    # Add placeholder circle
    ET.SubElement(add_drawing, "circle", {
        "style": "fill:#000000;stroke:#000000;stroke-width:0.015;stroke-dasharray:0.18, 0.18",
        "id": "path1",
        "cx": "0",
        "cy": "0",
        "r": "10",
        "inkscape:label": "placeholder-deleteme"
    })

    contents = ET.SubElement(svg, "g", {"id": "connector-drawing-contents-end"})

    #save the SVG to a file
    tree = ET.ElementTree(svg)
    # Convert the ElementTree to a string
    rough_string = ET.tostring(tree.getroot(), encoding="UTF-8")
    # Parse the string into a DOM object
    parsed = xml.dom.minidom.parseString(rough_string)
    # Pretty-print the DOM object
    pretty_svg = parsed.toprettyxml(indent="  ")
    # Write the formatted SVG to a file
    with open(filename, "w", encoding="UTF-8") as file:
        file.write(pretty_svg)


def tblock(
    library,
    name,
    size
    ):
    # === Parameters ===
    page_size = [11 * 96, 8.5 * 96]
    outer_margin = 20
    inner_margin = 40
    tick_spacing = 96
    tb_origin_offset = (398, 48)
    row_heights = [24, 24]
    column_widths = [
        [264, 50, 84],
        [73, 126, 139, 60]
    ]
    label_offset = (2, 7)
    key_offset_y = 16
    cell_texts = [
        [("DESCRIPTION", "tblock-key-desc"), ("REV", "tblock-key-rev"), ("RELEASE TICKET", "tblock-key-releaseticket")],
        [("SCALE", "tblock-key-scale"), ("PART NUMBER", "tblock-key-pn"),
         ("DRAWN BY", "tblock-key-drawnby"), ("SHEET", "tblock-key-sheet")]
    ]

    width, height = page_size
    svg = ET.Element('svg', {
        "xmlns": "http://www.w3.org/2000/svg",
        "version": "1.1",
        "width": str(width),
        "height": str(height)
    })

    contents_group = ET.SubElement(svg, "g", {"id": "tblock-contents-start"})

    def add_rect(parent, x, y, w, h, stroke="black", fill="none", stroke_width=1):
        ET.SubElement(parent, "rect", {
            "x": str(x),
            "y": str(y),
            "width": str(w),
            "height": str(h),
            "fill": fill,
            "stroke": stroke,
            "stroke-width": str(stroke_width)
        })

    def add_text(parent, x, y, text, size=8, anchor="start", bold=False, id=None):
        style = f"font-size:{size}px;font-family:Arial"
        if bold:
            style += ";font-weight:bold"
        attrs = {
            "x": str(x),
            "y": str(y),
            "style": style,
            "text-anchor": anchor,
        }
        if id:
            attrs["id"] = id
        ET.SubElement(parent, "text", attrs).text = text

    # === Border Group ===
    border_group = ET.SubElement(contents_group, "g", {"id": "border"})

    x_ticks = int((width - 2 * inner_margin) // tick_spacing)
    for i in range(x_ticks):
        x0 = inner_margin + i * tick_spacing
        x1 = x0 + tick_spacing
        x_center = (x0 + x1) / 2

        ET.SubElement(border_group, "line", {
            "x1": str(x0), "y1": str(outer_margin),
            "x2": str(x0), "y2": str(height - outer_margin),
            "stroke": "black", "stroke-width": "0.5"
        })

        label_y_top = (outer_margin + inner_margin) / 2
        label_y_bot = height - label_y_top
        add_text(border_group, x_center, label_y_top, str(i + 1), anchor="middle")
        add_text(border_group, x_center, label_y_bot, str(i + 1), anchor="middle")

    x_end = inner_margin + x_ticks * tick_spacing
    ET.SubElement(border_group, "line", {
        "x1": str(x_end), "y1": str(outer_margin),
        "x2": str(x_end), "y2": str(height - outer_margin),
        "stroke": "black", "stroke-width": "0.5"
    })

    y_ticks = int((height - 2 * inner_margin) // tick_spacing)
    for j in range(y_ticks):
        y0 = inner_margin + j * tick_spacing
        y1 = y0 + tick_spacing
        y_center = (y0 + y1) / 2

        ET.SubElement(border_group, "line", {
            "x1": str(outer_margin), "y1": str(y0),
            "x2": str(width - outer_margin), "y2": str(y0),
            "stroke": "black", "stroke-width": "0.5"
        })

        label = chr(ord('A') + j)
        label_x_left = (outer_margin + inner_margin) / 2
        label_x_right = width - label_x_left
        add_text(border_group, label_x_left, y_center + 4, label, anchor="middle")
        add_text(border_group, label_x_right, y_center + 4, label, anchor="middle")

    y_end = inner_margin + y_ticks * tick_spacing
    ET.SubElement(border_group, "line", {
        "x1": str(outer_margin), "y1": str(y_end),
        "x2": str(width - outer_margin), "y2": str(y_end),
        "stroke": "black", "stroke-width": "0.5"
    })

    add_rect(border_group, outer_margin, outer_margin, width - 2 * outer_margin, height - 2 * outer_margin)
    add_rect(border_group, inner_margin, inner_margin,
             width - 2 * inner_margin, height - 2 * inner_margin,
             stroke="black", fill="white", stroke_width=1)

    # === Logo Group ===
    tb_origin_x = width - inner_margin - tb_origin_offset[0]
    tb_origin_y = height - inner_margin - tb_origin_offset[1]
    logo_width = 1.25 * 96
    logo_height = sum(row_heights)
    logo_group = ET.SubElement(contents_group, "g", {"id": "logo"})
    add_rect(logo_group,
             tb_origin_x - logo_width,
             tb_origin_y,
             logo_width,
             logo_height,
             stroke="black", fill="none")

    # === Titleblock Cell Groups ===
    y_cursor = tb_origin_y
    for row_idx, row_height in enumerate(row_heights):
        row_cols = column_widths[row_idx]
        row_cells = cell_texts[row_idx]
        x_cursor = tb_origin_x
        for col_idx, col_width in enumerate(row_cols):
            label, key_id = row_cells[col_idx]
            group_id = label.lower().replace(" ", "-") if label else f"cell-r{row_idx}-c{col_idx}"
            cell_group = ET.SubElement(contents_group, "g", {"id": group_id})
            add_rect(cell_group, x_cursor, y_cursor, col_width, row_height)

            if label:
                add_text(cell_group,
                         x_cursor + label_offset[0],
                         y_cursor + label_offset[1],
                         label, size=7, bold=True)
            if key_id:
                center_x = x_cursor + col_width / 2
                add_text(cell_group,
                         center_x,
                         y_cursor + key_offset_y,
                         key_id, size=7, anchor="middle", id=key_id)

            x_cursor += col_width
        y_cursor += row_height

    # === Write SVG with indentation ===
    ET.SubElement(svg, "g", {"id": "tblock-contents-end"})
    rough_string = ET.tostring(svg, encoding="utf-8")
    pretty = minidom.parseString(rough_string).toprettyxml(indent="  ")
    with open(os.path.join(os.getcwd(), filename), "w", encoding="utf-8") as f:
        f.write(pretty)
