import os
import csv
import re
from harnice import fileio, component_library, svg_utils, instances_list

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
row_height = 0.16 * 96
font_size = 8
font_family = "Arial, Helvetica, sans-serif"
line_width = 0.008 * 96  # Define line_width before it is used

# Initialize an empty list to hold valid data rows
data_rows = []

# Read instances for buildnotes
for instance in instances_list.read_instance_rows():
    if instance.get("item_type") == "Buildnote":
        buildnote_number = instance.get("note_number")
        note = instance.get("note_text")

        has_shape = False
        if instance.get("mpn") not in ["", None]:
            has_shape = True
        if has_shape:
            shape = instance.get("mpn")
            lib_repo = instance.get("lib_repo")

        # Pull bubble from the library if there is a shape
        if has_shape and shape and lib_repo:
            component_library.pull_item_from_library(
                lib_repo=lib_repo,
                product="flagnotes",
                mpn=shape,
                destination_directory=path("buildnotes table bubbles"),
                item_name=f"bubble{buildnote_number}",
                quiet=True,
            )

        # Append row information only if it contains valid data
        data_rows.append(
            {"buildnote_number": buildnote_number, "note": note, "has_shape": has_shape}
        )

num_rows = len(data_rows)  # Number of valid data rows
svg_width = sum(column_widths)
svg_height = num_rows * row_height

# === Begin SVG Output ===
svg_lines = [
    f'<svg width="{svg_width}" height="{svg_height}" xmlns="http://www.w3.org/2000/svg" '
    f'font-family="{font_family}" font-size="{font_size}">',
    '<g id="buildnotes-table-contents-start">',
    f'<rect x="0" y="0" width="{svg_width}" height="{svg_height}" fill="none" stroke="black" stroke-width="{line_width}"/>',
]

# Column positions
bubble_x = 0
note_x = column_widths[0]

# === Merged Header Row ===
# Create a merged header cell that spans both columns
merged_header_x = 0
merged_header_width = sum(column_widths)  # Span the entire width of the columns
header_text_y = row_height / 2

# Draw the merged header cell (spanning across both columns)
svg_lines.append(
    f'<rect x="{merged_header_x}" y="0" width="{merged_header_width}" height="{row_height}" '
    f'style="fill:#e0e0e0;stroke:black;stroke-width:{line_width}"/>'
)

# Add text inside the merged header cell (center-justified)
svg_lines.append(
    f'<text x="{merged_header_x + merged_header_width / 2}" y="{header_text_y}" text-anchor="middle" '
    f'style="fill:black;dominant-baseline:middle;font-weight:bold;'
    f'font-family:{font_family};font-size:{font_size}">BUILD NOTES</text>'
)

# Initialize current_y to start below the header (current_y = row_height)
current_y = row_height  # Start from the row directly below the header

# === Data Rows ===
for row_index, row in enumerate(data_rows):
    # Adjust row height based on whether there is a bubble
    row_height_adjusted = (
        row_height if not row["has_shape"] else 0.4 * 96
    )  # Height for rows with bubbles
    y = current_y  # Current y position for the row
    cy = y + row_height_adjusted / 2  # Center of the cell vertically

    # Draw the cell borders for the current row
    for col_index, key in enumerate(["buildnote_number", "note"]):
        x = sum(column_widths[:col_index])
        text = row.get(key, "").strip()

        # Draw rectangle for the cell (border for all cells)
        svg_lines.append(
            f'<rect x="{x}" y="{y}" width="{column_widths[col_index]}" height="{row_height_adjusted}" '
            f'style="fill:white;stroke:black;stroke-width:{line_width}"/>'
        )

        # For the note column, left justify the text
        if key == "note":
            text_x = x + 5  # Add a small margin to the left for note text
            svg_lines.append(
                f'<text x="{text_x}" y="{cy}" text-anchor="start" '
                f'style="fill:black;dominant-baseline:middle;'
                f'font-family:{font_family};font-size:{font_size}">{text}</text>'
            )
        else:
            # Center the text for the buildnote number column
            svg_lines.append(
                f'<text x="{x + column_widths[col_index] / 2}" y="{cy}" text-anchor="middle" '
                f'style="fill:black;dominant-baseline:middle;'
                f'font-family:{font_family};font-size:{font_size}">{text}</text>'
            )

    # If row has a shape (bubble), add the bubble
    if row["has_shape"]:
        buildnote_number = row["buildnote_number"]
        svg_lines.append(
            f'<g id="bubble{buildnote_number}" transform="translate({bubble_x + column_widths[0] / 2},{cy})">'
        )
        svg_lines.append(f'  <g id="bubble{buildnote_number}-contents-start">')
        svg_lines.append(f"  </g>")
        svg_lines.append(f'  <g id="bubble{buildnote_number}-contents-end"/>')
        svg_lines.append(f"</g>")

    # Update the current_y position for the next row
    current_y += row_height_adjusted  # Move down after drawing the row

svg_lines.append("</g>")
svg_lines.append('<g id="buildnotes-table-contents-end"/>')
svg_lines.append("</svg>")

# === Write SVG Output ===
with open(path("buildnotes table svg"), "w", encoding="utf-8") as svg_file:
    svg_file.write("\n".join(svg_lines))

# === Inject bubble SVGs into the written file ===
for row in data_rows:
    if not row["has_shape"]:
        continue

    buildnote_number = row["buildnote_number"]
    source_svg_filepath = os.path.join(
        path("buildnotes table bubbles"), f"bubble{buildnote_number}-drawing.svg"
    )
    target_svg_filepath = path("buildnotes table svg")
    group_name = f"bubble{buildnote_number}"

    # Replace text placeholder "flagnote-text" → buildnote_number
    if os.path.exists(source_svg_filepath):
        with open(source_svg_filepath, "r", encoding="utf-8") as f:
            svg_text = f.read()

        updated_text = re.sub(
            r">\s*flagnote-text\s*<", f">{buildnote_number}<", svg_text
        )

        with open(source_svg_filepath, "w", encoding="utf-8") as f:
            f.write(updated_text)

    # Inject the bubble SVG into the target SVG file
    svg_utils.find_and_replace_svg_group(
        target_svg_filepath=target_svg_filepath,
        source_svg_filepath=source_svg_filepath,
        source_group_name=group_name,
        destination_group_name=group_name,
    )
