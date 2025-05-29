import os
import json
import xml.etree.ElementTree as ET
from dotenv import load_dotenv, dotenv_values
import os
import xml.etree.ElementTree as ET
from xml.dom import minidom
from harnice import(
    rev_history,
    cli,
    fileio
)

def part(library, mfgmpn):
    load_dotenv()

    library_path = os.getenv(library)
    if not library_path:
        raise ValueError(
            f"Environment variable '{library}' is not set. Add the path to this library from your harnice root directory."
        )

    part_directory = os.path.join(library_path, "parts", mfgmpn)

    if os.path.exists(part_directory):
        if cli.prompt("File already exists. Do you want to remove it?", "no") == "no":
            print("Exiting harnice")
            exit()
        else:
            import shutil
            shutil.rmtree(part_directory)
    
    os.makedirs(part_directory)

    cwd = os.getcwd()
    os.chdir(part_directory)
    fileio.verify_revision_structure()

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

    attributes_blank_json_path = os.path.join(fileio.rev_directory(), f"{mfgmpn}-attributes.json")

    if os.path.exists(attributes_blank_json_path):
        os.remove(attributes_blank_json_path)

    with open(attributes_blank_json_path, "w") as json_file:
        json.dump(attributes_blank_json, json_file, indent=4)

    #======== MAKE NEW PART SVG ===========
    svg_width = 400
    svg_height = 400

    # === SVG Init ===
    svg = ET.Element('svg', {
        "xmlns": "http://www.w3.org/2000/svg",
        "version": "1.1",
        "width": str(svg_width),
        "height": str(svg_height),
    })

    # === Group Start ===
    contents_group = ET.SubElement(svg, "g", {"id": "tblock-contents-start"})

    # === Rectangle ===
    ET.SubElement(contents_group, "rect", {
        "x": str(0),
        "y": str(-48),
        "width": str(96),
        "height": str(96),
        "fill": "#ccc",
        "stroke": "black",
        "stroke-width": "1"
    })

    # === Group End ===
    ET.SubElement(svg, "g", {"id": "tblock-contents-end"})

    # === Write SVG ===
    rough_string = ET.tostring(svg, encoding="utf-8")
    pretty = minidom.parseString(rough_string).toprettyxml(indent="  ")
    attributes_blank_json_path = os.path.join(fileio.rev_directory(), f"{mfgmpn}-drawing.svg")

    with open(attributes_blank_json_path, "w", encoding="utf-8") as f:
        f.write(pretty)

    os.chdir(cwd)

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
