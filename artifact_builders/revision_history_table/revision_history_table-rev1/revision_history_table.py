import os
import csv
import re
from harnice import (
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
column_headers = ["REVISION", "CHANGES", "STATUS", "DRAWN BY", "CHECKED BY", "STARTED", "MODIFIED"]
column_keys = ["rev", "revisionupdates", "status", "drawnby", "checkedby", "datestarted", "datemodified"]
column_widths = [0.5 * 96, 1.5 * 96, 0.6 * 96, 0.75 * 96, 0.75 * 96, 0.4 * 96, 0.4 * 96]
header_row_height = 0.2 * 96  # Height for the header row
normal_row_height = 0.2 * 96  # Default height for rows without bubbles
bubble_row_height = 0.4 * 96  # Height for rows with bubbles
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

# Calculate SVG height based on the number of rows
num_rows = len(data_rows) + 1  # Include header row
svg_width = sum(column_widths)
svg_height = header_row_height + sum(bubble_row_height if row["has_bubble"] else normal_row_height for row in data_rows)

svg_lines = [
    f'<svg width="{svg_width}" height="{svg_height}" xmlns="http://www.w3.org/2000/svg" '
    f'font-family="{font_family}" font-size="{font_size}">',
    '<g id="revision-history-table-contents-start">',
    f'<rect x="0" y="0" width="{svg_width}" height="{svg_height}" fill="none"/>'
]

# Header (draw borders for header cells as well)
current_y = 0  # Start from the top of the SVG for the header
for col_index, header in enumerate(column_headers):
    x = sum(column_widths[:col_index])
    y = current_y + header_row_height / 2  # Center the header text vertically
    # Draw the rectangle for the header cell
    svg_lines.append(
        f'<rect x="{x}" y="{current_y}" width="{column_widths[col_index]}" height="{header_row_height}" '
        f'style="fill:#d3d3d3;stroke:black;stroke-width:{line_width}"/>'
    )
    # Center the text inside each header cell
    svg_lines.append(
        f'<text x="{x + column_widths[col_index] / 2}" y="{y}" text-anchor="middle" '
        f'style="fill:black;dominant-baseline:middle;font-weight:bold;'
        f'font-family:{font_family};font-size:{font_size}">{header}</text>'
    )

# Update current_y to move down after the header
current_y += header_row_height

# Data Rows (draw borders for data cells as well)
for row_index, row in enumerate(data_rows):
    # Adjust row height based on whether there is a bubble
    row_height = bubble_row_height if row["has_bubble"] else normal_row_height
    y = current_y  # Current y position for the row
    cy = y + row_height / 2  # Center of the cell vertically

    for col_index, key in enumerate(column_keys):
        x = sum(column_widths[:col_index])
        text = row.get(key, "").strip()

        # Draw rectangle for the cell (border for all cells)
        svg_lines.append(
            f'<rect x="{x}" y="{y}" width="{column_widths[col_index]}" height="{row_height}" '
            f'style="fill:white;stroke:black;stroke-width:{line_width}"/>'
        )

        # Add text inside each cell (centered)
        svg_lines.append(
            f'<text x="{x + column_widths[col_index] / 2}" y="{cy}" text-anchor="middle" '
            f'style="fill:black;dominant-baseline:middle;'
            f'font-family:{font_family};font-size:{font_size}">{text}</text>'
        )

        # If there is a bubble, add the bubble SVG
        if key == "rev" and row["has_bubble"]:
            # Center the bubble within the cell
            bubble_x = x + column_widths[col_index] / 2  # Horizontally center the bubble
            bubble_y = cy - 3  # Vertically center the bubble plus an offset
            svg_lines.append(f'<g id="bubble{row["rev"]}" transform="translate({bubble_x},{bubble_y})">')
            svg_lines.append(f'  <g id="bubble{row["rev"]}-contents-start">')
            svg_lines.append(f'    <polygon points="0.0,19.2 -16.63,-9.6 16.63,-9.6" fill="#FFFFFF" stroke="#000000"/>')
            svg_lines.append(f'    <text x="0" y="0" style="font-size:8px;font-family:Arial" text-anchor="middle" dominant-baseline="middle">{row["rev"]}</text>')
            svg_lines.append(f'  </g>')
            svg_lines.append(f'  <g id="bubble{row["rev"]}-contents-end"/>')
            svg_lines.append(f'</g>')

    # Move the current_y position for the next row
    current_y += row_height

svg_lines.append('</g>')
svg_lines.append('<g id="revision-history-table-contents-end"/>')
svg_lines.append('</svg>')

# Write the base SVG
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
