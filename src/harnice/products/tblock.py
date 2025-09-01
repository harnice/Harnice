import os
import json
import xml.etree.ElementTree as ET
from xml.dom import minidom
import random
import math
import runpy
import re
from harnice import (
    instances_list,
    svg_utils,
    rev_history,
    fileio,
    cli
)

def render():
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
