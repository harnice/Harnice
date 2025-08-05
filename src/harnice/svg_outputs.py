import os
import re
import csv
import json
import math
import shutil
from os.path import basename
from inspect import currentframe
from collections import defaultdict
from dotenv import load_dotenv
from harnice import (
    fileio,
    svg_utils,
    instances_list,
    component_library
)

def prep_buildnotes_table():
    # === Configuration ===
    column_widths = [0.5 * 96, 3.375 * 96]  # bubble, then note
    row_height = 0.25 * 96
    font_size = 8
    font_family = "Arial, Helvetica, sans-serif"

    # === Output directories ===
    os.makedirs(fileio.dirpath("buildnotes_table"), exist_ok=True)
    os.makedirs(fileio.dirpath("buildnote_table_bubbles"), exist_ok=True)

    # === Read "buildnotes list" TSV ===
    with open(fileio.path("buildnotes list"), "r", newline="", encoding="utf-8") as tsv_file:
        reader = csv.DictReader(tsv_file, delimiter="\t")
        data_rows = []
        for row in reader:
            buildnote_number = row.get("buildnote_number", "").strip()
            note = row.get("note", "").strip()
            has_shape = row.get("has_shape", "").strip().lower() == "true"
            shape = row.get("shape", "").strip()
            supplier = row.get("shape_supplier", "").strip()

            if has_shape and shape and supplier:
                component_library.pull_item_from_library(
                    supplier=supplier,
                    lib_subpath="flagnotes",
                    mpn=shape,
                    destination_directory=fileio.dirpath("buildnote_table_bubbles"),
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
    with open(fileio.path("buildnotes table svg"), "w", encoding="utf-8") as svg_file:
        svg_file.write("\n".join(svg_lines))

    # === Inject bubble SVGs into the written file ===
    for row in data_rows:
        if not row["has_shape"]:
            continue

        buildnote_number = row["buildnote_number"]
        source_svg_filepath = os.path.join(fileio.dirpath("buildnote_table_bubbles"), f"bubble{buildnote_number}-drawing.svg")
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

def prep_revision_table():
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
                    destination_directory=fileio.dirpath("revision_table_bubbles"),
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
        '<g id="revhistory-table-contents-start">',
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
    svg_lines.append('<g id="revhistory-table-contents-end"/>')
    svg_lines.append('</svg>')

    # Write base SVG
    target_svg = fileio.path("revhistory master svg")
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
            fileio.dirpath("revision_table_bubbles"),
            f"bubble{rev_text}-drawing.svg"
        )
        target_svg_filepath = fileio.path("revhistory master svg")
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


