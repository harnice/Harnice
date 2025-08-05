import os
import csv
import re
from harnice import(
    fileio,
    component_library,
    svg_utils
)

artifact_mpn = "revision_history_table"

def path(target_value):
    if target_value == "revision table bubbles":
        return os.path.join(artifact_path, "revision_table_bubbles")
    if target_value == "revhistory master svg":
        return os.path.join(artifact_path, "revision-history-table-master.svg")
    else:
        raise KeyError(f"Filename {target_value} not found in {artifact_mpn} file tree")

os.makedirs(path("revision table bubbles"), exist_ok=True)

# === Configuration ===
column_headers = ["", "Checked By", "Drawn By", "Modified", "Started", "Status", "Rev"]
column_keys = ["", "checkedby", "drawnby", "datemodified", "datestarted", "status", "rev"]
column_widths = [0.5 * -96, 0.6 * -96, 0.6 * -96, 0.6 * -96, 0.6 * -96, 0.4 * -96, 0.4 * -96]
row_height = 0.2 * 96
font_size = 8
font_family = "Arial, Helvetica, sans-serif"
line_width = 0.008 * 96

# === Read "revision history" TSV ===
with open(fileio.path("revision history"), newline="", encoding="utf-8") as tsv_file:
    reader = csv.DictReader(tsv_file, delimiter="\t")
    data_rows = []
    for row in reader:
        rev = row.get("rev", "").strip()
        has_bubble = bool(row.get("affectedinstances", "").strip())
        if has_bubble:
            component_library.pull_item_from_library(
                supplier="public",
                lib_subpath="flagnotes",
                mpn="rev_change_callout",
                destination_directory=path("revision table bubbles"),
                item_name=f"bubble{rev}",
                quiet=True
            )
        row["has_bubble"] = has_bubble
        data_rows.append(row)

num_rows = len(data_rows) + 1  # header
svg_width = sum(column_widths)
svg_height = num_rows * row_height

svg_lines = [
    f'<svg width="{svg_width}" height="{svg_height}" xmlns="http://www.w3.org/2000/svg" '
    f'font-family="{font_family}" font-size="{font_size}">',
    '<g id="revision-history-table-contents-start">',
    f'<rect x="0" y="0" width="{svg_width}" height="{svg_height}" fill="none"/>'
]

# Header
for col_index, header in enumerate(column_headers):
    x = sum(column_widths[:col_index])
    y = row_height / 2
    svg_lines.append(
        f'<text x="{x}" y="{y}" text-anchor="start" '
        f'style="fill:black;dominant-baseline:middle;font-weight:bold;'
        f'font-family:{font_family};font-size:{font_size}">{header}</text>'
    )

# Data Rows
for row_index, row in enumerate(data_rows):
    y = (row_index + 1) * row_height
    cy = y + row_height / 2

    is_header_row = (row_index == 0)
    rect_fill = "#e0e0e0" if is_header_row else "white"
    font_weight = "bold" if is_header_row else "normal"

    for col_index, key in enumerate(column_keys):
        x = sum(column_widths[:col_index])
        text = row.get(key, "").strip()

        svg_lines.append(
            f'<rect x="{x}" y="{y}" width="{column_widths[col_index]}" height="{row_height}" '
            f'style="fill:{rect_fill};stroke:black;stroke-width:{line_width}"/>'
        )
        if key == "rev" and row["has_bubble"]:
            svg_lines.append(f'<g id="bubble{row["rev"]}" transform="translate({x+2},{cy})">')
            svg_lines.append(f'  <g id="bubble{row["rev"]}-contents-start">')
            svg_lines.append(f'  </g>')
            svg_lines.append(f'  <g id="bubble{row["rev"]}-contents-end"/>')
            svg_lines.append(f'</g>')
        else:
            svg_lines.append(
                f'<text x="{x}" y="{cy}" text-anchor="start" '
                f'style="fill:black;dominant-baseline:middle;'
                f'font-family:{font_family};font-size:{font_size}">{text}</text>'
            )

svg_lines.append('</g>')
svg_lines.append('<g id="revision-history-table-contents-end"/>')
svg_lines.append('</svg>')

# Write base SVG
target_svg = path("revhistory master svg")
with open(target_svg, "w", encoding="utf-8") as f:
    f.write("\n".join(svg_lines))

# === Inject bubble SVGs into the written file ===
for row in data_rows:
    if not row.get("has_bubble", False):
        continue
    affected = row.get("affectedinstances", "").strip()
    has_bubble = bool(affected)
    if not has_bubble:
        continue
    rev_text = row.get("rev", "").strip()
    source_svg_filepath = os.path.join(
        path("revision table bubbles"),
        f"bubble{rev_text}-drawing.svg"
    )
    target_svg_filepath = path("revhistory master svg")
    group_name = f"bubble{rev_text}"

    # Replace text placeholder "flagnote-text" → rev_text
    with open(source_svg_filepath, "r", encoding="utf-8") as f:
        svg_text = f.read()

    updated_text = re.sub(r'>\s*flagnote-text\s*<', f'>{rev_text}<', svg_text)

    with open(source_svg_filepath, "w", encoding="utf-8") as f:
        f.write(updated_text)

    # Inject the bubble SVG
    svg_utils.find_and_replace_svg_group(
        target_svg_filepath=target_svg_filepath,
        source_svg_filepath=source_svg_filepath,
        source_group_name=group_name,
        destination_group_name=group_name
    )
