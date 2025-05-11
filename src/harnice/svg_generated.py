import os
import re
import csv
import json
import math
import shutil
from os.path import basename
from inspect import currentframe
from collections import defaultdict

import fileio
import wirelist
import svg_utils
import instances_list
import component_library

def make_new_formboard_master_svg():
    
    def calculate_formboard_location(instance_name):
        """
        Given an instance_name, recursively trace up the parent_csys chain 
        until reaching an instance with no parent_csys defined.

        After tracing, iterate back down the chain, performing the translate/rotate algorithm,
        but excluding the last instance (the input instance itself) from movement calculations.

        Returns:
            (component_x_pos, component_y_pos, component_angle)
        """
        instances = instances_list.read_instance_rows()
        instances_lookup = {row['instance_name']: row for row in instances}

        chain = []
        current = instance_name

        while current:
            chain.append(current)
            row = instances_lookup.get(current)
            if not row:
                break
            parent = row.get('parent_csys', '').strip()
            if not parent:
                break
            current = parent

        x_pos = 0.0
        y_pos = 0.0
        angle = 0.0  # degrees

        # Skip the last element (the starting instance)
        for name in reversed(chain[1:]):
            row = instances_lookup.get(name, {})
            
            translate_x = row.get('translate_x', '').strip()
            translate_y = row.get('translate_y', '').strip()
            rotate_csys = row.get('rotate_csys', '').strip()

            try:
                translate_x = float(translate_x) if translate_x else 0.0
            except ValueError:
                translate_x = 0.0
            
            try:
                translate_y = float(translate_y) if translate_y else 0.0
            except ValueError:
                translate_y = 0.0

            try:
                rotate_csys = float(rotate_csys) if rotate_csys else 0.0
            except ValueError:
                rotate_csys = 0.0

            rad = math.radians(angle)

            x_pos += math.cos(rad) * translate_x - math.sin(rad) * translate_y
            y_pos += math.sin(rad) * translate_x + math.cos(rad) * translate_y
            angle += rotate_csys

            #print(f"After {name}: {x_pos}, {y_pos}, {angle}")
        return x_pos, y_pos, angle

   #=================================================
   #FIRST, UPDATE SEGMENT INSTANCES
    instances = instances_list.read_instance_rows()

    for instance in instances:
        if instance.get("item_type") == "Segment":
            segment_name = instance.get("instance_name", "").strip()
            if not segment_name:
                continue

            try:
                # Get length and diameter in inches and convert to pixels
                length_in = float(instance.get("length", 0))
                diameter_in = float(instance.get("diameter", 1))
                length = 96 * length_in
                diameter = 96 * diameter_in

                outline_thickness = 0.05 * 96
                centerline_thickness = 0.015 * 96

                half_diameter = diameter / 2

                svg_content = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{length}" height="{diameter}" viewBox="0 {-half_diameter} {length} {diameter}">
                    <line x1="0" y1="0" x2="{length}" y2="0" stroke="black" stroke-width="{diameter}" />
                    <line x1="0" y1="0" x2="{length}" y2="0" stroke="white" stroke-width="{diameter - outline_thickness}" />
                    <line x1="0" y1="0" x2="{length}" y2="0" stroke="black" style="stroke-width:{centerline_thickness};stroke-dasharray:18,18;stroke-dashoffset:0" />
                </svg>'''
                segment_dir = os.path.join(fileio.dirpath("editable_component_data"), segment_name)
                os.makedirs(segment_dir, exist_ok=True)

                output_filename = os.path.join(segment_dir, f"{segment_name}-drawing.svg")

                with open(output_filename, 'w') as svg_file:
                    svg_file.write(svg_content)

                component_library.add_filename_to_drawing_instance_list(os.path.basename(segment_dir))

                print(f"Built segment SVG for segment {segment_name} (deleted existing if present)")

            except Exception as e:
                print(f"Error processing segment {segment_name}: {e}")
 
 #==========================
    #things that did not work in source svgs:
        #sodipodi:nodetypes
        #sodipodi:namedview
        #inkscape:namedview
        #visio namespace: (v:)
    filepath = fileio.path("formboard master svg")
    if os.path.exists(filepath):
        os.remove(filepath)

    instances = instances_list.read_instance_rows()
    excluded_item_types = {"Cable", "Node"}

    # Group instances by item_type
    grouped_instances = defaultdict(list)
    for instance in instances:
        item_type = instance.get("item_type", "").strip()
        if item_type and item_type not in excluded_item_types:
            grouped_instances[item_type].append(instance)

    # Prepare lines for SVG content
    content_lines = []
    for item_type, items in grouped_instances.items():
        content_lines.append(f'    <g id="{item_type}" inkscape:label="{item_type}">')
        for instance in items:
            instance_name = instance.get("instance_name", "")
            if not instance_name:
                continue

            x, y, angle = calculate_formboard_location(instance_name)

            try:
                inner_svg = component_library.copy_svg_data(instance_name)
            except Exception as e:
                raise RuntimeError(f"Failed to read SVG data for {instance_name}: {e}")

            px_x = x * 96
            px_y = y * 96

            if instance.get("absolute_rotation") != "":
                angle = float(instance.get("absolute_rotation"))

            #transform harnice csys (right-hand rule, ccw is positive angle, up is +), to svg csys (cw is positive angle, up is -)
            svg_px_x = px_x
            svg_px_y = -1 * px_y
            svg_angle = -1 * angle

            content_lines.append(f'      <g id="{instance_name}" inkscape:label="{instance_name}" transform="translate({svg_px_x},{svg_px_y}) rotate({svg_angle})">'
            )
            content_lines.append(inner_svg)
            content_lines.append('      </g>')
        content_lines.append('    </g>')

    # Write full SVG
    with open(filepath, 'w') as f:
        f.write('<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n')
        f.write('<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="1000" height="1000">\n')
        f.write('  <g id="formboard-master-contents-start">\n')
        f.writelines(line + '\n' for line in content_lines)
        f.write('  </g>\n')
        f.write('  <g id="formboard-master-contents-end">\n')
        f.write('  </g>\n')
        f.write('</svg>\n')
      
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
        '<g id="bom-contents-start">'
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
        rect_fill = "#e0e0e0" if is_header_row else "white"
        font_weight = "bold" if is_header_row else "normal"

        for col_index, cell in enumerate(row):
            x = column_x_positions[col_index]
            cell_width = column_widths[col_index]

            # Cell background
            svg_lines.append(
                f'<rect x="{x}" y="{y}" width="{cell_width}" height="{row_height}" '
                f'style="fill:{rect_fill};stroke:black;stroke-width:{line_width}"/>'
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
                f'style="fill:black;dominant-baseline:middle;font-weight:{font_weight};'
                f'font-family:{font_family};font-size:{font_size}">{cell}</text>'
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
                    f'style="fill:none;stroke:black;stroke-width:{line_width}"/>'
                )

    svg_lines.append('</g>')
    svg_lines.append('<g id="bom-contents-end"/>')
    svg_lines.append('</svg>')

    # === Write SVG Output ===
    with open(fileio.path("bom table master svg"), "w", encoding="utf-8") as svg_file:
        svg_file.write("\n".join(svg_lines))

def prep_wirelist():
    # === Layout Configuration ===
    WIRELIST_COLUMNS = wirelist.column_styles()
    col_width = 0.75 * 96  # 0.75 inch
    row_height = 0.25 * 96
    font_size = 8
    font_family = "Arial"
    start_x = 0
    start_y = 0

    # === Read TSV data ===
    path = fileio.path("wirelist no formats")
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        data_rows = list(reader)

    # === SVG Header ===
    svg_lines = [f'''<?xml version="1.0" encoding="UTF-8" standalone="no"?>
    <svg xmlns="http://www.w3.org/2000/svg" version="1.1" font-family="{font_family}" font-size="{font_size}">
    <g id="wirelist-contents-start">
    ''']

    # === Header Row ===
    for col_idx, col in enumerate(WIRELIST_COLUMNS):
        x = start_x + col_idx * col_width
        y = start_y
        svg_lines.append(f'''
    <rect x="{x}" y="{y}" width="{col_width}" height="{row_height}" fill="{col['fill']}" stroke="black" />
    <text x="{x + col_width/2}" y="{y + row_height/2}" fill="{col['font']}" text-anchor="middle" dominant-baseline="middle">{col['name']}</text>''')

    # === Data Rows ===
    for row_idx, row in enumerate(data_rows):
        y = start_y + (row_idx + 1) * row_height
        for col_idx, col in enumerate(WIRELIST_COLUMNS):
            x = start_x + col_idx * col_width
            text = row.get(col["name"], "")
            svg_lines.append(f'''
    <rect x="{x}" y="{y}" width="{col_width}" height="{row_height}" fill="white" stroke="black" />
    <text x="{x + col_width/2}" y="{y + row_height/2}" fill="black" text-anchor="middle" dominant-baseline="middle">{text}</text>''')

    # === Close content group and SVG ===
    svg_lines.append('</g>')
    svg_lines.append('<g id="wirelist-contents-end"/>')
    svg_lines.append('</svg>')

    # === Write File ===
    out_path = fileio.path("wirelist master svg")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(svg_lines))
