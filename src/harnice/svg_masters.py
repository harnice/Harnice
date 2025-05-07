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
    font_family = "Arial, Helvetica, sans-serif"
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
        f'<svg width="{svg_width}" height="{svg_height}" xmlns="http://www.w3.org/2000/svg" '
        f'font-family="{font_family}" font-size="{font_size}">',
        '<style>',
        '  rect.cell { fill: white; stroke: black; }',
        '  rect.header { fill: #e0e0e0; stroke: black; }',
        '  text { fill: black; dominant-baseline: middle; font-family: Arial, Helvetica, sans-serif; }',
        '  .header { font-weight: bold; }',
        '  circle { fill: none; stroke: black; }',
        '</style>'
    ]

    # Compute left edges for each column starting at origin and going left
    column_x_positions = []
    running_x = 0
    for width in column_widths:
        running_x += width
        column_x_positions.append(-running_x)

    # === Draw table from origin outward ===
    for row_index, row in enumerate(reversed(table_rows)):
        y = -1 * (row_index + 1) * row_height
        is_header_row = (row_index == 0)
        rect_class = "header" if is_header_row else "cell"
        text_class = "header" if is_header_row else ""

        for col_index, cell in enumerate(row):
            x = column_x_positions[col_index]
            cell_width = column_widths[col_index]

            # Cell background
            svg_lines.append(
                f'<rect x="{x}" y="{y}" width="{cell_width}" height="{row_height}" '
                f'class="{rect_class}" stroke-width="{line_width}"/>'
            )

            # Text alignment
            if col_index in (0, 1):  # center-aligned
                text_anchor = "middle"
                text_x = x + cell_width / 2
            else:  # left-aligned
                text_anchor = "start"
                text_x = x + 5

            text_y = y + row_height / 2
            svg_lines.append(
                f'<text x="{text_x}" y="{text_y}" text-anchor="{text_anchor}" '
                f'class="{text_class}">{cell}</text>'
            )

            # Circle on ITEM column (not header row)
            is_item_column = (col_index == 0)
            is_data_row = not is_header_row
            if is_item_column and is_data_row:
                circle_cx = x + cell_width / 2
                circle_cy = y + row_height / 2
                radius = min(cell_width, row_height) / 2 - 2

                svg_lines.append(
                    f'<circle cx="{circle_cx}" cy="{circle_cy}" r="{radius}" '
                    f'stroke-width="{line_width}"/>'
                )

    svg_lines.append('</svg>')

    # === Write SVG Output ===
    with open(fileio.path("bom table master svg"), "w", encoding="utf-8") as svg_file:
        svg_file.write("\n".join(svg_lines))

def prep_tblock():
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

    # === Read Page Setup File ===
    with open(fileio.path("harnice output contents"), "r", encoding="utf-8") as f:  
        tblock_data = json.load(f)

    # === Generate Titleblock Master SVG ===
    for name, tblock in tblock_data.get("titleblocks", {}).items():
        supplier = tblock.get("supplier")
        titleblock = tblock.get("titleblock")
        text_map = tblock.get("text_replacements", {})

        destination_svg_name = f"{fileio.partnumber('pn-rev')}.{name}_master.svg"
        destination_svg_path = os.path.join(fileio.dirpath("master_svgs"), destination_svg_name)

        # Copy the library file into editable location
        component_library.pull_file_from_lib(
            supplier,
            os.path.join("titleblocks", titleblock, f"{titleblock}.svg"),
            destination_svg_path
        )

        # Replace text in the SVG
        with open(destination_svg_path, "r", encoding="utf-8") as f:
            svg = f.read()

        with open(fileio.path("harnice output contents"), "r", encoding="utf-8") as f:
            harnice_output_contents = json.load(f)

        for old, new in text_map.items():
            if new.startswith("pull_from_revision_history(") and new.endswith(")"):
                field_name = new[len("pull_from_revision_history("):-1]
                if field_name not in revision_row:
                    raise KeyError(f"[ERROR] Field '{field_name}' not found in revision history")
                new = revision_row[field_name]
                if not new:
                    raise ValueError(f"[ERROR] Field '{field_name}' is empty in revision history")
            
            if new.startswith("pull_from_harnice_output_contents(") and new.endswith(")"):
                field_name = new[len("pull_from_harnice_output_contents("):-1]
                if field_name != "formboard.scale":
                    raise KeyError(f"[ERROR] You're trying to pull something from harnice output contents that is not defined {field_name}")
                new = harnice_output_contents.get("formboard", {}).get("scale", 1)
                #convert to str
                new = f'{new:.3f}'
                if not new:
                    raise ValueError(f"Scale is empty in {fileio.name("harnice output contents")}")

            if old not in svg:
                print(f"[WARN] key '{old}' not found in title block")

            svg = svg.replace(old, new)

        with open(destination_svg_path, "w", encoding="utf-8") as f:
            f.write(svg)

def update_output_contents():
    # === Titleblock Defaults ===
    blank_setup = {
        "titleblocks": {
            "tblock1": {
                "supplier": "public",
                "titleblock": "harnice_tblock-11x8.5",
                "text_replacements": {
                    "tblock-key-desc": "",
                    "tblock-key-pn": "pull_from_revision_history(pn)",
                    "tblock-key-drawnby": "",
                    "tblock-key-rev": "pull_from_revision_history(rev)",
                    "tblock-key-releaseticket": "",
                    "tblock-key-scale": "A"
                }
            }
        },
        "formboards": {
            "formboard1": {
                "scale": "A",
                "hide_instances": []
            }
        },
        "scales:": {
            "A": 1
        }
    }

    # === Load or Initialize Titleblock Setup ===
    if not os.path.exists(fileio.path("harnice output contents")) or os.path.getsize(fileio.path("harnice output contents")) == 0:
        with open(fileio.path("harnice output contents"), "w", encoding="utf-8") as f:
            json.dump(blank_setup, f, indent=4)
        tblock_data = blank_setup
    else:
        try:
            with open(fileio.path("harnice output contents"), "r", encoding="utf-8") as f:
                tblock_data = json.load(f)
        except json.JSONDecodeError:
            with open(fileio.path("harnice output contents"), "w", encoding="utf-8") as f:
                json.dump(blank_setup, f, indent=4)
            tblock_data = blank_setup

    with open(fileio.path("harnice output contents"), "w", encoding="utf-8") as f:
        json.dump(tblock_data, f, indent=4)