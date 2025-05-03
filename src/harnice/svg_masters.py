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
    parent_dir = os.path.dirname(os.getcwd())
    tsv_path = os.path.join(parent_dir, f"{pn}-revision_history.tsv")

    if not os.path.isfile(tsv_path):
        print(f"[ERROR] {tsv_path} not found.")
        return

    with open(tsv_path, "r", encoding="utf-8") as file:
        header = file.readline().strip().split('\t')
        json_tblock_data = {}

        for line in file:
            row = line.strip().split('\t')
            padded_row = row + [""] * (len(header) - len(row))
            row_dict = dict(zip(header, padded_row))

            if row_dict.get("pn", "").strip() == pn and row_dict.get("rev", "").strip() == rev:
                json_tblock_data = row_dict
                break

    if not json_tblock_data:
        print(f"[ERROR] No matching revision row found for pn={pn}, rev={rev}")
        return

    # === Step 2: Prepare default tblock SVG ===
    wanted_tblock_libdomain = "rs"
    wanted_tblock_libsubpath = "page_defaults"
    wanted_tblock_libfilename = "rs-tblock-default.svg"
    library_used_tblock_filepath = os.path.join(
        os.getcwd(), "editable_component_data", wanted_tblock_libsubpath, wanted_tblock_libfilename
    )

    component_library.import_library_file(wanted_tblock_libdomain, wanted_tblock_libsubpath, wanted_tblock_libfilename)

    if os.path.exists(fileio.path("tblock master svg")):
        os.remove(fileio.path("tblock master svg"))

    shutil.copy(library_used_tblock_filepath, fileio.dirpath("master_svgs"))
    os.rename(
        os.path.join(fileio.dirpath("master_svgs"), wanted_tblock_libfilename),
        fileio.path("tblock master svg")
    )

    # === Step 3: Perform key substitution ===
    with open(fileio.path("tblock master svg"), 'r') as inf:
        content = inf.read()

    def replacer(match):
        key = match.group(1)
        old_text = match.group(0)
        new_text = str(json_tblock_data.get(key, old_text))
        print(f"Replacing: '{old_text}' with: '{new_text}'")
        return new_text

    updated_content = re.sub(r"tblock-key-(\w+)", replacer, content)

    with open(fileio.path("tblock master svg"), 'w') as outf:
        outf.write(updated_content)
        print("[INFO] tblock master svg updated successfully.")
