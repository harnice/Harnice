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
    wirelist,
    svg_utils,
    instances_list,
    component_library
)

def prep_formboard_drawings(page_setup_contents):
    
    def calculate_formboard_location(instance_name, origin):
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

        x_pos = origin[0]
        y_pos = origin[1]
        angle = origin[2]  # degrees

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

                svg_content = f'''
                <svg xmlns="http://www.w3.org/2000/svg" width="{length}" height="{diameter}" viewBox="0 {-half_diameter} {length} {diameter}">
                    <g id="{instance.get("instance_name")}-contents-start">
                        <line x1="0" y1="0" x2="{length}" y2="0" stroke="black" stroke-width="{diameter}" />
                        <line x1="0" y1="0" x2="{length}" y2="0" stroke="white" stroke-width="{diameter - outline_thickness}" />
                        <line x1="0" y1="0" x2="{length}" y2="0" stroke="black" style="stroke-width:{centerline_thickness};stroke-dasharray:18,18;stroke-dashoffset:0" />
                    </g>
                    <g id="{instance.get("instance_name")}-contents-end"></g>
                </svg>
                '''
                segment_dir = os.path.join(fileio.dirpath("uneditable_instance_data"), segment_name)
                os.makedirs(segment_dir, exist_ok=True)

                output_filename = os.path.join(segment_dir, f"{segment_name}-drawing.svg")

                with open(output_filename, 'w') as svg_file:
                    svg_file.write(svg_content)
                    
            except Exception as e:
                print(f"Error processing segment {segment_name}: {e}")
 
    #==========================
    for formboard_name in page_setup_contents.get("formboards", {}):
        filename = f"{fileio.partnumber("pn-rev")}.{formboard_name}.svg"
        filepath = os.path.join(fileio.dirpath("formboard_svgs"),filename)

        instances = instances_list.read_instance_rows()
        printable_item_types = {"Connector", "Backshell", "Segment", "Flagnote", "Flagnote leader"}

        rotation = page_setup_contents["formboards"].get(formboard_name, {}).get("rotation", 0)
        if rotation == "":
            raise KeyError(f"[ERROR] Rotation '{rotation}' not found in harnice output contents")
        origin = [0, 0, rotation]

        scale_name = page_setup_contents["formboards"].get(formboard_name, {}).get("scale", "A")
        scale = page_setup_contents["scales"].get(scale_name)

        # Group instances by item_type
        grouped_instances = defaultdict(list)
        for instance in instances:
            item_type = instance.get("item_type", "").strip()
            if item_type and item_type in printable_item_types:
                grouped_instances[item_type].append(instance)

        # Prepare lines for SVG content
        content_lines = []
        for item_type, items in grouped_instances.items():
            content_lines.append(f'    <g id="{item_type}" inkscape:label="{item_type}">')
            for instance in items:
                #cancel if hidden
                if instance.get("instance_name") in page_setup_contents["formboards"].get(formboard_name, {}).get("hide_instances", []):
                    continue

                instance_name = instance.get("instance_name", "")
                if not instance_name:
                    continue

                x, y, angle = calculate_formboard_location(instance_name, origin)

                px_x = x * 96
                px_y = y * 96

                if instance.get("absolute_rotation") != "":
                    angle = float(instance.get("absolute_rotation"))

                #segments are positioned using absolute rotation and are the only items that must be corrected for changes in origin orientation
                if instance.get("item_type") == "Segment":
                    angle += origin[2]

                #transform harnice csys (right-hand rule, ccw is positive angle, up is +), to svg csys (cw is positive angle, up is -)
                svg_px_x = px_x
                svg_px_y = -1 * px_y
                svg_angle = -1 * angle

                if not item_type == "Flagnote":
                    content_lines.append(f'      <g id="{instance_name}-contents-start" inkscape:label="{instance_name}-contents-start" transform="translate({svg_px_x},{svg_px_y}) rotate({svg_angle})">'
                    )
                    content_lines.append('      </g>')
                    content_lines.append(f'      <g id="{instance_name}-contents-end" inkscape:label="{instance_name}-contents-end"></g>')

                else:
                    content_lines.append(f'      <g id="{instance_name}-translate" transform="translate({svg_px_x},{svg_px_y}) rotate({svg_angle})">')
                    content_lines.append(f'        <g id="{instance_name}-scale" transform="scale({1 / scale})">')
                    content_lines.append(f'          <g id="{instance_name}-contents-start" inkscape:label="{instance_name}-contents-start">'
                    )
                    content_lines.append(f'          </g>')
                    content_lines.append(f'          <g id="{instance_name}-contents-end" inkscape:label="{instance_name}-contents-end"></g>')
                    content_lines.append(f'        </g>')
                    content_lines.append(f'      </g>')

            content_lines.append('    </g>')

        # Write full SVG
        with open(filepath, 'w') as f:
            f.write('<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n')
            f.write('<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="1000" height="1000">\n')
            f.write(f'  <g id="{formboard_name}-contents-start">\n')
            f.write(f'    <g id="{formboard_name}-scale_group" transform="scale({scale})">\n')
            f.writelines(line + '\n' for line in content_lines)
            f.write('    </g>\n')
            f.write('  </g>\n')
            f.write(f'  <g id="{formboard_name}-contents-end">\n')
            f.write('  </g>\n')
            f.write('</svg>\n')

        #now that the SVG has been written, copy the connector content in:
        for instance in instances:
            item_type = instance.get("item_type", "").strip()
            if item_type and item_type in printable_item_types:
                if item_type in {"Connector", "Backshell"}:
                    instance_data_dir = fileio.dirpath("editable_instance_data")
                elif item_type == "Flagnote leader":
                    instance_data_dir = os.path.join(fileio.dirpath("uneditable_instance_data"), formboard_name)
                else:
                    instance_data_dir = fileio.dirpath("uneditable_instance_data")

                svg_utils.find_and_replace_svg_group(
                    #target_svg_filepath
                    filepath,
                    #source_svg_filepath
                    os.path.join(
                        instance_data_dir, 
                        instance.get("instance_name"),
                        f"{instance.get("instance_name")}-drawing.svg"
                    ),
                    #source_group_name
                    instance.get("instance_name"),
                    #destination_group_name
                    instance.get("instance_name")
                )
      
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
    col_width = 76
    row_height = 12
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
    svg_lines = [
        f'''<?xml version="1.0" encoding="UTF-8" standalone="no"?>
         <svg xmlns="http://www.w3.org/2000/svg" version="1.1">
         <g id="wirelist-contents-start">
          ''']

    # === Header Row ===
    for col_idx, col in enumerate(WIRELIST_COLUMNS):
        x = start_x + col_idx * col_width
        y = start_y
        svg_lines.append(f'''
    <rect x="{x}" y="{y}" width="{col_width}" height="{row_height}" fill="{col['fill']}" stroke="black" />
    <text x="{x + col_width/2}" y="{y + row_height/2}" fill="{col['font']}" text-anchor="middle" dominant-baseline="middle" font-family="{font_family}" font-size="{font_size}">{col['name']}</text>''')

    # === Data Rows ===
    for row_idx, row in enumerate(data_rows):
        y = start_y + (row_idx + 1) * row_height
        for col_idx, col in enumerate(WIRELIST_COLUMNS):
            x = start_x + col_idx * col_width
            text = row.get(col["name"], "")
            svg_lines.append(f'''
    <rect x="{x}" y="{y}" width="{col_width}" height="{row_height}" fill="white" stroke="black" />
    <text x="{x + col_width/2}" y="{y + row_height/2}" fill="black" text-anchor="middle" dominant-baseline="middle" font-family="{font_family}" font-size="{font_size}">{text}</text>''')

    # === Close content group and SVG ===
    svg_lines.append('</g>')
    svg_lines.append('<g id="wirelist-contents-end"/>')
    svg_lines.append('</svg>')

    # === Write File ===
    out_path = fileio.path("wirelist master svg")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(svg_lines))

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
        svg_utils.find_and_replace_svg_group(
            project_svg_path,
            fileio.path("bom table master svg"),
            "bom", "bom"
        )
        svg_utils.find_and_replace_svg_group(
            project_svg_path,
            fileio.path("buildnotes table svg"),
            "buildnotes-table", "buildnotes-table"
        )
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

def update_harnice_output(page_setup_contents):
    for page_data in page_setup_contents.get("pages", []):
        page_name = page_data.get("name")
        filename = f"{fileio.partnumber('pn-rev')}.{page_name}.svg"
        filepath = os.path.join(fileio.dirpath("page_setup"), filename)

        #pull PDF size from json in library
        titleblock_supplier = page_data.get("supplier")
        titleblock = page_data.get("titleblock", {})
        attr_library_path = os.path.join(
            fileio.dirpath("tblock_svgs"),
            page_name,
            f"{page_name}-attributes.json"
        )
        with open(attr_library_path, "r", encoding="utf-8") as f:
            tblock_attributes = json.load(f)
        page_size_in = tblock_attributes.get("page_size_in", {})
        page_size_px = [page_size_in[0] * 96, page_size_in[1] * 96]
        
        if not os.path.exists(filepath):
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(
                    #<?xml version="1.0" encoding="UTF-8" standalone="no"?>
                    f"""
        <svg xmlns="http://www.w3.org/2000/svg"
            xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape"
            version="1.1"
            width="{page_size_px[0]}"
            height="{page_size_px[1]}">
            <g id="tblock-svg-contents-start">
            </g>
            <g id="tblock-svg-contents-end"></g>
            <g id="svg-master-contents-start">
            </g>
            <g id="svg-master-contents-end"></g>
        </svg>
        """)

        #replace the master svg
        svg_utils.find_and_replace_svg_group(
            filepath, 
            fileio.path("master svg"), 
            "svg-master", 
            "svg-master"
        )

        #replace the titleblock
        svg_utils.find_and_replace_svg_group(
            filepath, 
            os.path.join(fileio.dirpath("tblock_svgs"), page_name, f"{page_name}.svg"),
            page_name, 
            "tblock-svg"
        )

def update_page_setup_json():
    # === Titleblock Defaults ===
    blank_setup = {
        "pages": [
            {
                "name": "page1",
                "supplier": "public",
                "titleblock": "harnice_tblock-11x8.5",
                "text_replacements": {
                    "tblock-key-desc": "pull_from_revision_history(desc)",
                    "tblock-key-pn": "pull_from_revision_history(pn)",
                    "tblock-key-drawnby": "pull_from_revision_history(drawnby)",
                    "tblock-key-rev": "pull_from_revision_history(rev)",
                    "tblock-key-releaseticket": "",
                    "tblock-key-scale": "A",
                    "tblock-key-sheet": "autosheet"
                }
            }
        ],
        "formboards": {
            "formboard1": {
                "scale": "A",
                "rotation": 0,
                "hide_instances": []
            }
        },
        "scales": {
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

    return tblock_data

def prep_buildnotes_table():
    # === Configuration ===
    column_widths = [0.5 * 96, 3.375 * 96]  # bubble, then note
    row_height = 0.35 * 96
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
        rev = row.get("rev", "").strip()
        source_svg_filepath = os.path.join(
            fileio.dirpath("revision_table_bubbles"),
            f"bubble{rev}-drawing.svg"
        )
        target_svg_filepath = fileio.path("revhistory master svg")
        group_name = f"bubble{rev}"

        # Replace text placeholder "flagnote-text" → rev
        with open(source_svg_filepath, "r", encoding="utf-8") as f:
            svg_text = f.read()

        updated_text = re.sub(r'>\s*flagnote-text\s*<', f'>{rev}<', svg_text)

        with open(source_svg_filepath, "w", encoding="utf-8") as f:
            f.write(updated_text)

        # Inject the bubble SVG
        svg_utils.find_and_replace_svg_group(
            target_svg_filepath=target_svg_filepath,
            source_svg_filepath=source_svg_filepath,
            source_group_name=group_name,
            destination_group_name=group_name
        )


