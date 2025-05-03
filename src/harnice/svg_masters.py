import csv
import fileio
import os
import shutil
import re
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
    # === Step 1: Load revision row from TSV ===
    pn = fileio.partnumber("pn")
    rev = fileio.partnumber("R")

    if not os.path.isfile(fileio.path("revision history")):
        raise FileNotFoundError(f"[ERROR] {fileio.path('revision_history')} not found.")

    revision_row = {}
    with open(fileio.path("revision history"), "r", encoding="utf-8") as file:
        header = file.readline().strip().split('\t')
        for line in file:
            row = line.strip().split('\t')
            padded_row = row + [""] * (len(header) - len(row))
            row_dict = dict(zip(header, padded_row))

            if row_dict.get("pn", "").strip() == pn and row_dict.get("rev", "").strip() == rev:
                revision_row = {k: v.strip() for k, v in row_dict.items()}
                break

    if not revision_row:
        raise ValueError(f"[ERROR] No matching revision row found for pn={pn}, rev={rev}")

    # === Step 2: Load or initialize JSON ===
    if os.path.isfile(fileio.path("tblock master text")):
        with open(fileio.path("tblock master text"), "r", encoding="utf-8") as jf:
            json_tblock_data = json.load(jf)
    else:
        json_tblock_data = {}

    # Update JSON with non-empty revision history fields
    json_tblock_data.update({k: v for k, v in revision_row.items() if v})

    with open(fileio.path("tblock master text"), "w", encoding="utf-8") as jf:
        json.dump(json_tblock_data, jf, indent=2)

    # === Step 3: Check tblock source fields ===
    tblock_supplier = revision_row.get("tblock_supplier", "").strip()
    tblock_name = revision_row.get("tblock", "").strip()

    if not tblock_supplier or not tblock_name:
        print(f"[INFO] Skipping tblock import and SVG update due to missing tblock or tblock_supplier.")
        return

    # === Step 4: Import from library and update SVG ===
    component_library.update_tblock_from_lib(tblock_supplier, tblock_name)

    if not os.path.isfile(fileio.path("tblock master svg")):
        raise FileNotFoundError(f"[ERROR] Expected SVG file not found: {fileio.path('tblock master svg')}")

    with open(fileio.path("tblock master svg"), 'r', encoding="utf-8") as inf:
        content = inf.read()

    def replacer(match):
        key = match.group(1)
        old_text = match.group(0)
        new_text = str(json_tblock_data.get(key, old_text))
        print(f"Replacing: '{old_text}' with: '{new_text}'")
        return new_text

    updated_content = re.sub(r"tblock-key-(\w+)", replacer, content)

    with open(fileio.path("tblock master svg"), 'w', encoding="utf-8") as outf:
        outf.write(updated_content)

    print("[INFO] tblock master svg updated successfully.")
