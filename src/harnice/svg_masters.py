import csv
import fileio
import os
import shutil
import re
import json
from inspect import currentframe
from os.path import basename
import component_library

def prep_bom():
    # === Configuration ===
    selected_columns = ["bom_line_number", "qty", "total_length_exact", "mpn"]
    header_labels = ["ITEM", "QTY", "LENGTH", "MPN"]
    column_widths = [0.375 * 96, 0.375 * 96, 0.75 * 96, 1.75 * 96]  # in pixels
    row_height = 0.16 * 96
    font_size = 8
    font_family = "Arial"
    line_width = 0.008 * 96

    # === Read TSV Data ===
    with open(fileio.path("harness bom"), "r", newline="", encoding="utf-8") as tsv_file:
        reader = csv.DictReader(tsv_file, delimiter="\t")
        data_rows = [
            [row.get(col, "") for col in selected_columns]
            for row in reader
            if row.get("bom_line_number", "").isdigit()
        ]

    # Sort and append header at the bottom (last row)
    data_rows.sort(key=lambda r: int(r[0]))
    table_rows = data_rows + [header_labels]

    num_rows = len(table_rows)
    svg_width = sum(column_widths)
    svg_height = num_rows * row_height

    # === Begin SVG Output ===
    svg_lines = [
        f'<svg width="{svg_width}" height="{svg_height}" '
        f'font-family="{font_family}" font-size="{font_size}">',
        '<g id="bom-master-contents-start">'
    ]

    # Compute left edges for each column starting at origin and going left
    column_x_positions = []
    running_x = 0
    for width in column_widths:
        running_x += width
        column_x_positions.append(-running_x)

    # === Draw table from origin outward ===
    for row_index, row in enumerate(reversed(table_rows)):
        y = -1 * (row_index + 1) * row_height  # Upward from origin
        for col_index, cell in enumerate(row):
            x = column_x_positions[col_index]
            cell_width = column_widths[col_index]

            # Cell background
            svg_lines.append(
                f'<rect x="{x}" y="{y}" width="{cell_width}" height="{row_height}" '
                f'fill="white" stroke="black" stroke-width="{line_width}"/>'
            )

            # Text alignment
            if col_index in (0, 1):  # center-aligned
                text_anchor = "middle"
                text_x = x + cell_width / 2
            else:  # left-aligned
                text_anchor = "start"
                text_x = x + 5

            text_y = y + row_height / 2
            is_header_row = (row_index == 0)
            font_weight = 'bold' if is_header_row else 'normal'

            svg_lines.append(
                f'<text x="{text_x}" y="{text_y}" fill="black" '
                f'text-anchor="{text_anchor}" dominant-baseline="middle" '
                f'font-weight="{font_weight}">{cell}</text>'
            )

            # Circle on ITEM column (not header row)
            is_item_column = (col_index == 0)
            is_data_row = (row_index != 0)
            if is_item_column and is_data_row:
                circle_cx = x + cell_width / 2
                circle_cy = y + row_height / 2
                radius = min(cell_width, row_height) / 2 - 2

                svg_lines.append(
                    f'<circle cx="{circle_cx}" cy="{circle_cy}" r="{radius}" '
                    f'fill="none" stroke="black" stroke-width="{line_width}"/>'
                )

    svg_lines.append('</g>')
    svg_lines.append('<g id="bom-master-contents-end"></g>')
    svg_lines.append('</svg>')

    # === Write SVG Output ===
    with open(fileio.path("bom table master svg"), "w", encoding="utf-8") as svg_file:
        svg_file.write("\n".join(svg_lines))

def prep_tblock():
    # === Titleblock Defaults ===
    default_supplier = "public"
    default_lib_file = "library-tblock-11x8.5-border"
    default_position = [-10 * 96, 0]
    tblock_name = "tblock1"

    # === Define Blank Setup ===
    blank_setup = {
        "titleblocks": {
            tblock_name: {
                "supplier": default_supplier,
                "lib_file": default_lib_file,
                "default_position": default_position,
                "text_replacements": {
                    "tblock-key-desc": "",
                    "tblock-key-pn": "pull_from_revision_history(pn)",
                    "tblock-key-drawnby": "",
                    "tblock-key-rev": "pull_from_revision_history(rev)",
                    "tblock-key-releaseticket": ""
                }
            }
        }
    }

    # === Load or Initialize Titleblock Setup ===
    if not os.path.exists(fileio.path("titleblock setup")) or os.path.getsize(fileio.path("titleblock setup")) == 0:
        with open(fileio.path("titleblock setup"), "w", encoding="utf-8") as f:
            json.dump(blank_setup, f, indent=4)
        tblock_data = blank_setup
    else:
        try:
            with open(fileio.path("titleblock setup"), "r", encoding="utf-8") as f:
                tblock_data = json.load(f)
        except json.JSONDecodeError:
            with open(fileio.path("titleblock setup"), "w", encoding="utf-8") as f:
                json.dump(blank_setup, f, indent=4)
            tblock_data = blank_setup

    # === Load revision row for current part/revision ===
    revision_row = {}
    if os.path.exists(fileio.path("revision history")):
        with open(fileio.path("revision history"), "r", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter="\t")
            for row in reader:
                if row.get("rev") == fileio.partnumber("R"):
                    revision_row = {k: (v or "").strip() for k, v in row.items()}
                    break

    if not revision_row:
        raise ValueError(f"[ERROR] No revision row found for rev '{fileio.partnumber('R')}' in revision history")

    # === Save Updated Titleblock Setup ===
    with open(fileio.path("titleblock setup"), "w", encoding="utf-8") as f:
        json.dump(tblock_data, f, indent=4)

    # === Generate Titleblock Master SVG ===
    for name, tblock in tblock_data.get("titleblocks", {}).items():
        supplier = tblock.get("supplier")
        lib_file = tblock.get("lib_file")
        text_map = tblock.get("text_replacements", {})

        svg_name = f"{fileio.partnumber('pn-rev')}.{name}_master.svg"
        svg_path = os.path.join(fileio.dirpath("master_svgs"), svg_name)

        # Copy the library file into editable location
        component_library.pull_file_from_lib(
            supplier,
            os.path.join("titleblocks", f"{lib_file}.svg"),
            svg_path
        )

        # Replace text in the SVG
        with open(svg_path, "r", encoding="utf-8") as f:
            svg = f.read()

        for old, new in text_map.items():
            if new.startswith("pull_from_revision_history(") and new.endswith(")"):
                field_name = new[len("pull_from_revision_history("):-1]
                if field_name not in revision_row:
                    raise KeyError(f"[ERROR] Field '{field_name}' not found in revision history")
                new = revision_row[field_name]
                if not new:
                    raise ValueError(f"[ERROR] Field '{field_name}' is empty in revision history")

            if old not in svg:
                print(f"[WARN] key '{old}' not found in title block")

            svg = svg.replace(old, new)

        with open(svg_path, "w", encoding="utf-8") as f:
            f.write(svg)
