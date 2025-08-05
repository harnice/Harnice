import os
import csv
import re
from harnice import (
    fileio,
    component_library,
    svg_utils,
    instances_list
)

artifact_mpn = "buildnotes_table"

def path(target_value):
    if target_value == "buildnotes table bubbles":
        return os.path.join(artifact_path, "bom_table_bubbles")
    if target_value == "buildnotes table svg":
        return os.path.join(artifact_path, "buildnotes-table-master.svg")
    if target_value == "buildnotes list":
        return os.path.join(artifact_path, "buildnotes-list.tsv")
    else:
        raise KeyError(f"Filename {target_value} not found in {artifact_mpn} file tree")

os.makedirs(path("buildnotes table bubbles"), exist_ok=True)

# === Configuration ===
column_widths = [0.5 * 96, 3.375 * 96]  # bubble, then note
row_height = 0.25 * 96
font_size = 8
font_family = "Arial, Helvetica, sans-serif"

# Start with an empty header row instead of None
data_rows = [{
    "buildnote_number": "",
    "note": "",
    "has_shape": False
}]

for instance in instances_list.read_instance_rows():
    if instance.get("item_type") == "Buildnote":
        buildnote_number = instance.get("bubble_text", "").strip()
        note = instance.get("note_text", "").strip()
        has_shape = instance.get("mpn", "").strip().lower() == "true"
        shape = instance.get("mpn", "").strip()
        supplier = instance.get("supplier", "").strip()

        if has_shape and shape and supplier:
            component_library.pull_item_from_library(
                supplier=supplier,
                lib_subpath="flagnotes",
                mpn=shape,
                destination_directory=path("buildnotes table bubbles"),  # ✅ fixed
                item_name=f"bubble{buildnote_number}",
                quiet=True
            )

        data_rows.append({
            "buildnote_number": buildnote_number,
            "note": note,
            "has_shape": has_shape
        })

num_rows = len(data_rows) + 1  # +1 for header row
svg_width = sum(column_widths)
svg_height = num_rows * row_height

# === Begin SVG Output ===
svg_lines = [
    f'<svg width="{svg_width}" height="{svg_height}" xmlns="http://www.w3.org/2000/svg" '
    f'font-family="{font_family}" font-size="{font_size}">',
    '<g id="buildnotes-table-contents-start">',
    f'<rect x="0" y="0" width="{svg_width}" height="{svg_height}" fill="none"/>'
]

# Column positions
bubble_x = 0
note_x = column_widths[0]

# === Header Row ===
header_text_x = 10
header_text_y = row_height / 2
svg_lines.append(
    f'<text x="{header_text_x}" y="{header_text_y}" text-anchor="start" '
    f'style="fill:black;dominant-baseline:middle;font-weight:bold;'
    f'font-family:{font_family};font-size:{font_size}">BUILD NOTES</text>'
)

# === Data Rows ===
for row_index, row in enumerate(data_rows):
    y = (row_index + 1) * row_height
    cx = bubble_x + column_widths[0] / 2
    cy = y + row_height / 2

    buildnote_number = row["buildnote_number"]
    note_text = row["note"]
    has_shape = row["has_shape"]

    if has_shape:
        svg_lines.append(f'<g id="bubble{buildnote_number}" transform="translate({cx},{cy})">')
        svg_lines.append(f'  <g id="bubble{buildnote_number}-contents-start">')
        svg_lines.append(f'  </g>')
        svg_lines.append(f'  <g id="bubble{buildnote_number}-contents-end"/>')
        svg_lines.append(f'</g>')
    else:
        svg_lines.append(
            f'<text x="{cx}" y="{cy}" text-anchor="middle" '
            f'style="fill:black;dominant-baseline:middle;'
            f'font-family:{font_family};font-size:{font_size}">{buildnote_number}</text>'
        )

    # Draw note text
    text_x = note_x + 5
    text_y = cy
    svg_lines.append(
        f'<text x="{text_x}" y="{text_y}" text-anchor="start" '
        f'style="fill:black;dominant-baseline:middle;'
        f'font-family:{font_family};font-size:{font_size}">{note_text}</text>'
    )

svg_lines.append('</g>')
svg_lines.append('<g id="buildnotes-table-contents-end"/>')
svg_lines.append('</svg>')

# === Write SVG Output ===
with open(path("buildnotes table svg"), "w", encoding="utf-8") as svg_file:
    svg_file.write("\n".join(svg_lines))

# === Inject bubble SVGs into the written file ===
for row in data_rows:
    if not row["has_shape"]:
        continue

    buildnote_number = row["buildnote_number"]
    source_svg_filepath = os.path.join(fileio.dirpath("buildnotes table bubbles"), f"bubble{buildnote_number}-drawing.svg")
    target_svg_filepath = fileio.path("buildnotes table svg")
    group_name = f"bubble{buildnote_number}"

    # Replace text placeholder "flagnote-text" → buildnote_number
    if os.path.exists(source_svg_filepath):
        with open(source_svg_filepath, "r", encoding="utf-8") as f:
            svg_text = f.read()

        updated_text = re.sub(r'>\s*flagnote-text\s*<', f'>{buildnote_number}<', svg_text)

        with open(source_svg_filepath, "w", encoding="utf-8") as f:
            f.write(updated_text)

    # Inject the bubble SVG
    svg_utils.find_and_replace_svg_group(
        target_svg_filepath=target_svg_filepath,
        source_svg_filepath=source_svg_filepath,
        source_group_name=group_name,
        destination_group_name=group_name
    )
