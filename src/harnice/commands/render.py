import os
import json
import xml.etree.ElementTree as ET
from xml.dom import minidom
import random
import math
import runpy
from harnice import (
    run_wireviz,
    wirelist,
    instances_list,
    svg_utils,
    flagnotes,
    formboard,
    rev_history,
    component_library,
    fileio,
    svg_outputs,
    cli,
    feature_tree
)

def harness():
    print("Thanks for using Harnice!")

    # === Step 1: Verify revision and file structure at the top level ===
    fileio.verify_revision_structure()
    fileio.verify_yaml_exists()
    fileio.generate_structure()

    # === Step 2: Ensure feature_tree.py exists ===
    feature_tree_path = fileio.path("feature tree")
    if not os.path.exists(feature_tree_path):
        feature_tree.generate_default_feature_tree()

    # === Step 3: Run the project-specific feature_tree.py ===
    runpy.run_path(feature_tree_path, run_name="__main__")

    print(f"Harnice: harness {fileio.partnumber('pn')} rendered successfully!")
    print()

def tblock():
    print("Warning: rendering a titleblock may clear user edits to its svg. Do you wish to proceed?")
    if cli.prompt("Press enter to confirm or any key to exit") == "":
        exit()

    # === Default Parameters ===
    params = {
        "page_size": [11 * 96, 8.5 * 96],
        "outer_margin": 20,
        "inner_margin": 40,
        "tick_spacing": 96,
        "tb_origin_offset": [398, 48],
        "row_heights": [24, 24],
        "column_widths": [
            [264, 50, 84],
            [73, 126, 139, 60]
        ],
        "label_offset": [2, 7],
        "key_offset_y": 16,
        "cell_texts": [
            [("DESCRIPTION", "tblock-key-desc"), ("REV", "tblock-key-rev"), ("RELEASE TICKET", "tblock-key-releaseticket")],
            [("SCALE", "tblock-key-scale"), ("PART NUMBER", "tblock-key-pn"),
             ("DRAWN BY", "tblock-key-drawnby"), ("SHEET", "tblock-key-sheet")]
        ]
    }

    fileio.verify_revision_structure()

    # === If param file doesn't exist, create it ===
    if not os.path.exists(fileio.path("params")):
        with open(fileio.path("params"), "w", encoding="utf-8") as f:
            json.dump(params, f, indent=2)
        #if it does exist, ignore it

    # === Load parameters from JSON ===
    with open(fileio.path("params"), "r", encoding="utf-8") as f:
        p = json.load(f)

    width, height = p["page_size"]
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

    x_ticks = int((width - 2 * p["inner_margin"]) // p["tick_spacing"])
    for i in range(x_ticks):
        x0 = p["inner_margin"] + i * p["tick_spacing"]
        x_center = x0 + p["tick_spacing"] / 2
        ET.SubElement(border_group, "line", {
            "x1": str(x0), "y1": str(p["outer_margin"]),
            "x2": str(x0), "y2": str(height - p["outer_margin"]),
            "stroke": "black", "stroke-width": "0.5"
        })
        label_y_top = (p["outer_margin"] + p["inner_margin"]) / 2
        label_y_bot = height - label_y_top
        add_text(border_group, x_center, label_y_top, str(i + 1), anchor="middle")
        add_text(border_group, x_center, label_y_bot, str(i + 1), anchor="middle")

    x_end = p["inner_margin"] + x_ticks * p["tick_spacing"]
    ET.SubElement(border_group, "line", {
        "x1": str(x_end), "y1": str(p["outer_margin"]),
        "x2": str(x_end), "y2": str(height - p["outer_margin"]),
        "stroke": "black", "stroke-width": "0.5"
    })

    y_ticks = int((height - 2 * p["inner_margin"]) // p["tick_spacing"])
    for j in range(y_ticks):
        y0 = p["inner_margin"] + j * p["tick_spacing"]
        y_center = y0 + p["tick_spacing"] / 2
        ET.SubElement(border_group, "line", {
            "x1": str(p["outer_margin"]), "y1": str(y0),
            "x2": str(width - p["outer_margin"]), "y2": str(y0),
            "stroke": "black", "stroke-width": "0.5"
        })
        label = chr(ord('A') + j)
        label_x_left = (p["outer_margin"] + p["inner_margin"]) / 2
        label_x_right = width - label_x_left
        add_text(border_group, label_x_left, y_center + 4, label, anchor="middle")
        add_text(border_group, label_x_right, y_center + 4, label, anchor="middle")

    y_end = p["inner_margin"] + y_ticks * p["tick_spacing"]
    ET.SubElement(border_group, "line", {
        "x1": str(p["outer_margin"]), "y1": str(y_end),
        "x2": str(width - p["outer_margin"]), "y2": str(y_end),
        "stroke": "black", "stroke-width": "0.5"
    })

    add_rect(border_group, p["outer_margin"], p["outer_margin"], width - 2 * p["outer_margin"], height - 2 * p["outer_margin"])
    add_rect(border_group, p["inner_margin"], p["inner_margin"], width - 2 * p["inner_margin"], height - 2 * p["inner_margin"], stroke="black", fill="white", stroke_width=1)

    # === Logo Group ===
    tb_origin_x = width - p["inner_margin"] - p["tb_origin_offset"][0]
    tb_origin_y = height - p["inner_margin"] - p["tb_origin_offset"][1]
    logo_width = 1.25 * 96
    logo_height = sum(p["row_heights"])
    logo_group = ET.SubElement(contents_group, "g", {"id": "logo"})
    add_rect(logo_group, tb_origin_x - logo_width, tb_origin_y, logo_width, logo_height)

    # === Titleblock Cell Groups ===
    y_cursor = tb_origin_y
    for row_idx, row_height in enumerate(p["row_heights"]):
        row_cols = p["column_widths"][row_idx]
        row_cells = p["cell_texts"][row_idx]
        x_cursor = tb_origin_x
        for col_idx, col_width in enumerate(row_cols):
            label, key_id = row_cells[col_idx]
            group_id = label.lower().replace(" ", "-") if label else f"cell-r{row_idx}-c{col_idx}"
            cell_group = ET.SubElement(contents_group, "g", {"id": group_id})
            add_rect(cell_group, x_cursor, y_cursor, col_width, row_height)

            if label:
                add_text(cell_group,
                         x_cursor + p["label_offset"][0],
                         y_cursor + p["label_offset"][1],
                         label, size=7, bold=True)
            if key_id:
                center_x = x_cursor + col_width / 2
                add_text(cell_group,
                         center_x,
                         y_cursor + p["key_offset_y"],
                         key_id, size=7, anchor="middle", id=key_id)

            x_cursor += col_width
        y_cursor += row_height

    ET.SubElement(svg, "g", {"id": "tblock-contents-end"})
    rough_string = ET.tostring(svg, encoding="utf-8")
    pretty = minidom.parseString(rough_string).toprettyxml(indent="  ")
    with open(fileio.path("drawing"), "w", encoding="utf-8") as f:
        f.write(pretty)

    # === Write attributes file ===
    periphery_json = {
        "periphery_locs": {
            "bom_loc": [tb_origin_x, tb_origin_y],  # same as bottom-left of titleblock
            "buildnotes_loc": [0, 0],  # same as bottom-left of titleblock
            "revhistory_loc": [0, 0]  # same as bottom-left of titleblock
        },
        "page_size_in": [
            round(p["page_size"][0] / 96, 3),
            round(p["page_size"][1] / 96, 3)
        ]
    }

    with open(fileio.path("attributes"), "w", encoding="utf-8") as f:
        json.dump(periphery_json, f, indent=2)

    print()
    print(f"Titleblock '{fileio.partnumber("pn")}' updated")
    print()

def part():
    fileio.verify_revision_structure()

    # === ATTRIBUTES JSON SETUP ===
    default_attributes = {
        "plotting_info": {
            "csys_parent_prefs": [".node"],
            "component_translate_inches": {
                "translate_x": 0,
                "translate_y": 0,
                "rotate_csys": 0
            }
        },
        "tooling_info": {"tools": []},
        "build_notes": [],
        "flagnote_locations": [
            {"angle": a, "distance": 2, "arrowhead_angle": "", "arrowhead_distance": 1}
            for a in [0, 15, -15, 30, -30, 45, -45, 60, -60, -75, 75, -90, 90, -105, 105, -120]
        ]
    }

    attributes_path = fileio.path("attributes")
    merged_attributes = default_attributes.copy()

    if os.path.exists(attributes_path):
        try:
            with open(attributes_path, "r", encoding="utf-8") as f:
                existing = json.load(f)
            for key, val in existing.items():
                if key in merged_attributes and isinstance(merged_attributes[key], dict) and isinstance(val, dict):
                    merged_attributes[key].update(val)
                else:
                    merged_attributes[key] = val
        except Exception as e:
            print(f"[WARNING] Could not load existing attributes.json: {e}")

    with open(attributes_path, "w", encoding="utf-8") as f:
        json.dump(merged_attributes, f, indent=4)

    # === SVG SETUP ===
    svg_path = fileio.path("drawing")
    temp_svg_path = svg_path + ".tmp"

    svg_width = 400
    svg_height = 400
    group_name = f"{fileio.partnumber('pn')}-drawing"

    random_fill = "#{:06X}".format(random.randint(0, 0xFFFFFF))
    fallback_rect = f'    <rect x="0" y="-48" width="96" height="96" fill="{random_fill}" stroke="black" stroke-width="1"/>'

    try:
        with open(attributes_path, "r", encoding="utf-8") as f:
            attrs = json.load(f)
        flagnote_locations = attrs.get("flagnote_locations", [])
    except Exception as e:
        print(f"[WARNING] Could not read flagnote_locations: {e}")
        flagnote_locations = []

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="{svg_width}" height="{svg_height}">',
        f'  <g id="{group_name}-contents-start">',
        fallback_rect,
        '  </g>',
        f'  <g id="{group_name}-contents-end">',
        '  </g>',
    ]

    lines.append(f'  <g id="flagnote locations">')

    for i, entry in enumerate(flagnote_locations):
        try:
            angle_deg = float(entry.get("angle", 0))
            distance_in = float(entry.get("distance", 0))
            angle_rad = math.radians(angle_deg)
            dist_px = distance_in * 96
            x = dist_px * math.cos(angle_rad)
            y = -dist_px * math.sin(angle_rad)

            arrow_angle_deg = float(entry.get("arrowhead_angle") or angle_deg)
            arrow_dist_in = float(entry.get("arrowhead_distance", 1))
            arrow_rad = math.radians(arrow_angle_deg)
            arrow_dist_px = arrow_dist_in * 96
            arrow_x = arrow_dist_px * math.cos(arrow_rad)
            arrow_y = -arrow_dist_px * math.sin(arrow_rad)

            lines.append(f'    <circle cx="{x:.2f}" cy="{y:.2f}" r="12" fill="#444" stroke="black" stroke-width="1"/>')
            lines.append(f'    <text x="{x:.2f}" y="{y+4:.2f}" fill="white" font-size="12" font-family="sans-serif" text-anchor="middle">{i+1}</text>')
            lines.append(f'    <line x1="{x:.2f}" y1="{y:.2f}" x2="{arrow_x:.2f}" y2="{arrow_y:.2f}" stroke="black" stroke-width="1"/>')

            dx = arrow_x - x
            dy = arrow_y - y
            length = math.hypot(dx, dy)
            if length == 0:
                continue
            ux = dx / length
            uy = dy / length
            px = -uy
            py = ux
            base_x = arrow_x - ux * 6
            base_y = arrow_y - uy * 6
            tip = (arrow_x, arrow_y)
            left = (base_x + px * 2, base_y + py * 2)
            right = (base_x - px * 2, base_y - py * 2)

            lines.append(
                f'    <polygon points="{tip[0]:.2f},{tip[1]:.2f} {left[0]:.2f},{left[1]:.2f} {right[0]:.2f},{right[1]:.2f}" fill="black"/>'
            )
        except Exception as e:
            print(f"[WARNING] Failed to render flagnote {i}: {e}")

    lines.append('  </g>')
    lines.append('</svg>')

    with open(temp_svg_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    if os.path.exists(svg_path):
        try:
            with open(svg_path, "r", encoding="utf-8") as f:
                svg_text = f.read()
        except Exception:
            svg_text = ""

        if f"{group_name}-contents-start" not in svg_text or f"{group_name}-contents-end" not in svg_text:
            svg_utils.add_entire_svg_file_contents_to_group(svg_path, group_name)

        svg_utils.find_and_replace_svg_group(
            target_svg_filepath=temp_svg_path,
            source_svg_filepath=svg_path,
            source_group_name=group_name,
            destination_group_name=group_name
        )

    if os.path.exists(svg_path):
        os.remove(svg_path)
    os.rename(temp_svg_path, svg_path)

    print()
    print(f"Part file '{fileio.partnumber('pn')}' updated")
    print()

def flagnote():
    print("Warning: rendering a flagnote may clear user edits to its svg. Do you wish to proceed?")
    if cli.prompt("Press enter to confirm or any key to exit") == "":
        exit()

    fileio.verify_revision_structure()
    params_path = fileio.path("params")

    # Geometry generators
    def regular_ngon(n, radius=19.2, rotation_deg=0):
        angle_offset = math.radians(rotation_deg)
        return [
            [
                round(radius * math.cos(2 * math.pi * i / n + angle_offset), 2),
                round(radius * math.sin(2 * math.pi * i / n + angle_offset), 2)
            ]
            for i in range(n)
        ]

    def right_arrow():
        return [[-24, -12], [0, -12], [0, -24], [24, 0], [0, 24], [0, 12], [-24, 12]]

    def left_arrow():
        return [[24, -12], [0, -12], [0, -24], [-24, 0], [0, 24], [0, 12], [24, 12]]

    def flag_pennant():
        return [[-24, -12], [24, 0], [-24, 12]]

    # List of shape options with (label, generator)
    shape_options = [
        ("circle", None),
        ("square", lambda: regular_ngon(4, rotation_deg=45)),
        ("triangle", lambda: regular_ngon(3, rotation_deg=-90)),
        ("upside down triangle", lambda: regular_ngon(3, rotation_deg=90)),
        ("hexagon", lambda: regular_ngon(6)),
        ("pentagon", lambda: regular_ngon(5)),
        ("right arrow", right_arrow),
        ("left arrow", left_arrow),
        ("octagon", lambda: regular_ngon(8)),
        ("diamond", lambda: regular_ngon(4, rotation_deg=0)),
        ("flag / pennant", flag_pennant)
    ]

    # === Prompt shape if no params exist ===
    if not os.path.exists(params_path):
        print("No flagnote params found.")
        print("Choose a shape for your flagnote:")
        for i, (label, _) in enumerate(shape_options, 1):
            print(f"  {i}) {label}")

        while True:
            response = cli.prompt("Enter the number of your choice").strip()
            if response.isdigit():
                index = int(response)
                if 1 <= index <= len(shape_options):
                    shape_label, shape_func = shape_options[index - 1]
                    break
            print("Invalid selection. Please enter a number from the list.")

        params = {
            "fill": 0xFFFFFF,
            "border": 0x000000,
            "text inside": "flagnote-text"
        }

        if shape_func:
            params["vertices"] = shape_func()

        with open(params_path, "w", encoding="utf-8") as f:
            json.dump(params, f, indent=2)

    # === Load params ===
    with open(params_path, "r", encoding="utf-8") as f:
        p = json.load(f)

    svg_width = 6 * 96
    svg_height = 6 * 96
    group_name = "contents"

    fill = p.get("fill")
    if not isinstance(fill, int):
        fill = random.randint(0x000000, 0xFFFFFF)

    border = p.get("border", 0x000000)
    shape_svg = ""

    # === Shape element ===
    if "vertices" in p:
        if p["vertices"]:
            points_str = " ".join(f"{x},{y}" for x, y in p["vertices"])
            shape_svg = f'    <polygon points="{points_str}" fill="#{fill:06X}" stroke="#{border:06X}"/>\n'
    else:
        shape_svg = f'    <circle cx="0" cy="0" r="10" fill="#{fill:06X}" stroke="#{border:06X}"/>\n'

    # === Text element ===
    text_content = p.get("text inside", "")
    text_svg = (
        f'    <text x="0" y="0" '
        f'style="font-size:8px;font-family:Arial" '
        f'text-anchor="middle" dominant-baseline="middle" id="flagnote-text">{text_content}</text>\n'
    )

    contents = shape_svg + text_svg if shape_svg else ""

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="{svg_width}" height="{svg_height}">',
        f'  <g id="{fileio.partnumber('pn')}-drawing-contents-start">',
        contents.rstrip(),
        f'  </g>',
        f'  <g id="{fileio.partnumber('pn')}-drawing-contents-end">',
        f'  </g>',
        '</svg>'
    ]

    with open(fileio.path("drawing"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print()
    print(f"Flagnote '{fileio.partnumber('pn')}' updated")
    print()


def system():
    print("System-level rendering not yet implemented.")