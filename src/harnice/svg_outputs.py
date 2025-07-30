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

def prep_tblocks(page_setup_contents, revhistory_data):
    # === Validate page name uniqueness ===
    page_names = [p.get("name") for p in page_setup_contents.get("pages", [])]
    duplicates = {name for name in page_names if page_names.count(name) > 1}
    if duplicates:
        raise ValueError(f"[ERROR] Duplicate page name(s) found: {', '.join(duplicates)}")

    for page in page_setup_contents.get("pages", []):
        page_name = page.get("name")
        tblock_data = page  # each item in the list *is* the tblock_data
        if not tblock_data:
            raise KeyError(f"[ERROR] Titleblock '{page_name}' not found in harnice output contents")

        supplier_key = tblock_data.get("supplier")
        supplier_root = os.getenv(supplier_key)
        if not supplier_root:
            raise EnvironmentError(f"[ERROR] Environment variable '{supplier_key}' is not set")

        titleblock = tblock_data.get("titleblock")

        # === Prepare destination directory for used files ===
        destination_directory = os.path.join(fileio.dirpath("tblock_svgs"), page_name)

        # === Pull from library ===
        component_library.pull_item_from_library(
            supplier=supplier_key,
            lib_subpath="titleblocks",
            mpn=titleblock,
            destination_directory=destination_directory,
            used_rev=None,
            item_name=titleblock
        )

        # === Access pulled files ===
        attr_path = os.path.join(destination_directory, f"{page_name}-attributes.json")
        os.rename(os.path.join(destination_directory,f"{titleblock}-attributes.json"), attr_path)
        svg_path = os.path.join(destination_directory, f"{titleblock}.svg")

        if not os.path.isfile(attr_path):
            raise FileNotFoundError(f"[ERROR] Attribute file not found: {attr_path}")
        with open(attr_path, "r", encoding="utf-8") as f:
            tblock_attributes = json.load(f)

        # === Page size in pixels ===
        page_size_in = tblock_attributes.get("page_size_in", [11, 8.5])
        page_size_px = [int(page_size_in[0] * 96), int(page_size_in[1] * 96)]

        bom_loc = tblock_attributes.get("periphery_locs", {}).get("bom_loc", [0, 0])
        translate_bom = f'translate({bom_loc[0]},{bom_loc[1]})'

        buildnotes_loc = tblock_attributes.get("periphery_locs", {}).get("buildnotes_loc", [0, 0])
        translate_buildnotes = f'translate({buildnotes_loc[0]},{buildnotes_loc[1]})'

        revhistory_loc = tblock_attributes.get("periphery_locs", {}).get("revhistory_loc", [0, 0])
        translate_revhistory = f'translate({revhistory_loc[0]},{revhistory_loc[1]})'

        # === Prepare destination SVG ===
        project_svg_path = os.path.join(destination_directory, f"{page_name}.svg")

        svg = [
            '<?xml version="1.0" encoding="UTF-8" standalone="no"?>',
            f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" version="1.1" width="{page_size_px[0]}" height="{page_size_px[1]}">',
            f'  <g id="{page_name}-contents-start">',
            f'    <g id="tblock-contents-start"></g>',
            f'    <g id="tblock-contents-end"></g>',
            f'    <g id="bom" transform="{translate_bom}">',
            f'      <g id="bom-contents-start"></g>',
            f'      <g id="bom-contents-end"></g>',
            f'    </g>',
            f'    <g id="revhistory" transform="{translate_revhistory}">',
            f'      <g id="revhistory-table-contents-start"></g>',
            f'      <g id="revhistory-table-contents-end"></g>',
            f'    </g>',
            f'    <g id="buildnotes" transform="{translate_buildnotes}">',
            f'      <g id="buildnotes-table-contents-start"></g>',
            f'      <g id="buildnotes-table-contents-end"></g>',
            f'    </g>',
            f'  </g>',
            f'  <g id="{page_name}-contents-end"></g>',
            '</svg>'
        ]

        with open(project_svg_path, "w", encoding="utf-8") as f:
            f.write("\n".join(svg))

        # === Import tblock and bom SVG contents ===
        svg_utils.find_and_replace_svg_group(
            project_svg_path,
            os.path.join(destination_directory, f"{titleblock}-drawing.svg"),
            "tblock", "tblock"
        )
        if "bom" in page.get("show_items"):
            svg_utils.find_and_replace_svg_group(
                project_svg_path,
                fileio.path("bom table master svg"),
                "bom", "bom"
            )
        if "buildnotes" in page.get("show_items"):
            svg_utils.find_and_replace_svg_group(
                project_svg_path,
                fileio.path("buildnotes table svg"),
                "buildnotes-table", "buildnotes-table"
            )
        if "revhistory" in page.get("show_items"):
            svg_utils.find_and_replace_svg_group(
                project_svg_path,
                fileio.path("revhistory master svg"),
                "revhistory-table", "revhistory-table"
            )

        # === Text replacements ===
        text_map = tblock_data.get("text_replacements", {})
        with open(project_svg_path, "r", encoding="utf-8") as f:
            svg = f.read()

        for old, new in text_map.items():
            if new.startswith("pull_from_revision_history(") and new.endswith(")"):
                field_name = new[len("pull_from_revision_history("):-1]
                if field_name not in revhistory_data:
                    raise ValueError(f"[ERROR] Field '{field_name}' is missing from revision history")
                new = revhistory_data.get(field_name, "").strip()

            if "scale" in old.lower():
                scales_lookup = page_setup_contents.get("scales", {})
                new = f"{scales_lookup.get(new, 0):.3f}" if new in scales_lookup else ""

            if new == "autosheet":
                page_names = [p.get("name") for p in page_setup_contents.get("pages", [])]
                try:
                    page_num = page_names.index(page_name) + 1
                except ValueError:
                    raise ValueError(f"[ERROR] Page name '{page_name}' not found in pages list")
                total_pages = len(page_names)
                new = f"{page_num} of {total_pages}"

            if old not in svg:
                print(f"[WARN] Key '{old}' not found in titleblock SVG")

            svg = svg.replace(old, new)

        with open(project_svg_path, "w", encoding="utf-8") as f:
            f.write(svg)

def prep_master(page_setup_contents):
    translate = [0, -3200]
    delta_x_translate = 1600
    # === Build basic SVG contents ===
    svg = [
        '<?xml version="1.0" encoding="UTF-8" standalone="no"?>',
        '<svg xmlns="http://www.w3.org/2000/svg" version="1.1">',
        '  <g id="svg-master-contents-start">'
    ]

    # Add formboard placeholders
    for formboard_name in page_setup_contents.get("formboards", {}):
        translate_str = f"translate({translate[0]},{translate[1]})"
        svg += [
            f'    <g id="{formboard_name}" transform="{translate_str}">',
            f'      <g id="{formboard_name}-contents-start"></g>',
            f'      <g id="{formboard_name}-contents-end"></g>',
            f'    </g>'
        ]
        translate[0] += delta_x_translate

    # Add other master group placeholders
    translate_str = f"translate({translate[0]},{translate[1]})"
    svg += [
        f'    <g id="esch" transform="{translate_str}">',
        f'      <g id="esch-master-contents-start"></g>',
        f'      <g id="esch-master-contents-end"></g>',
        f'    </g>'
    ]
    translate[0] += delta_x_translate
    translate_str = f"translate({translate[0]},{translate[1]})"
    svg += [
        f'    <g id="wirelist" transform="{translate_str}">',
        f'      <g id="wirelist-contents-start"></g>',
        f'      <g id="wirelist-contents-end"></g>',
        f'    </g>'
        '  </g>',  # Close svg-master-contents-start
        '  <g id="svg-master-contents-end"></g>'
        '</svg>'
    ]

    # === Write SVG ===
    with open(fileio.path("master svg"), "w", encoding="utf-8") as f:
        f.write("\n".join(svg))


    # === Import stuff ===
    for formboard_name in page_setup_contents.get("formboards", {}):
        source_svg_name = f"{fileio.partnumber("pn-rev")}.{formboard_name}.svg"
        source_svg_path = os.path.join(fileio.dirpath("formboard_svgs"), source_svg_name)
        svg_utils.find_and_replace_svg_group(fileio.path("master svg"), source_svg_path, formboard_name, formboard_name)
    
    svg_utils.find_and_replace_svg_group(fileio.path("master svg"), fileio.path("esch master svg"), "esch-master", "esch-master")
    svg_utils.find_and_replace_svg_group(fileio.path("master svg"), fileio.path("wirelist master svg"), "wirelist", "wirelist")    

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


