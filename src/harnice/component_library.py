import xml.etree.ElementTree as ET
import math
import xml.dom.minidom
import os
import csv
import json
import fileio
import re
from dotenv import load_dotenv, dotenv_values
import instances_list
import harnice_prechecker
from os.path import basename
from inspect import currentframe
import shutil
import filecmp

#this list is used to keep track of all the valid instances:
drawing_instance_filenames = [None]
#when creating new instances, add to this list by add_filename_to_drawing_instance_list().
#directories in drawing-instances that are not named in this list will be deleted by delete_unmatched_files().

def pull_parts():
    load_dotenv()
    global drawing_instance_filenames
    supported_library_components = ['connector', 'backshell']
    instances = instances_list.read_instance_rows()

    updated_instances = []

    for instance in instances:
        print(f"Working {instance.get('instance_name')}")
        print(f"MPN: {instance.get('mpn')}")

        #if the type of instance is supported by harnice library
        if instance.get('item_type', '').lower() in supported_library_components:
            
            #find the highest rev in the library
            highest_rev = ""  # default
            try:
                with open(
                    os.path.join(
                        os.getenv(instance.get('supplier')),
                        "parts",
                        instance.get('mpn', ''),
                        f"{instance.get('mpn', '')}-revision_history.tsv"
                    ),
                    newline='', encoding='utf-8'
                ) as f:
                    reader = csv.DictReader(f, delimiter='\t')
                    for rev_entry in reader:
                        rev_str = rev_entry.get('rev', '').strip()
                        if rev_str.isdigit():
                            rev_num = int(rev_str)
                            if highest_rev == "" or rev_num > int(highest_rev):
                                highest_rev = str(rev_num)
            except FileNotFoundError:
                print(f"Missing revision history document. Update your library and rerun.")

            #see if that library instance has already been imported
            exists_bool, exists_rev = exists_in_lib_used(instance.get('instance_name'), instance.get('mpn'))
            print(f"Library for component is used in the project: {exists_bool}")
            if exists_bool:
                print(f"Library used for component has revision {exists_rev}")
            instance['lib_rev_used_here'] = exists_rev

            #find latest release in library
            print(f"Highest available rev in library is {highest_rev}")
            instance['lib_latest_rev'] = highest_rev

            # build paths
            mpn = instance.get('mpn')
            mpn_rev = f"{mpn}-rev{highest_rev}"
            source_lib_path = os.path.join(os.getenv(instance.get('supplier')), "parts", mpn, mpn_rev)
            target_directory = os.path.join(fileio.dirpath("editable_component_data"), instance.get('instance_name'), "library_used_do_not_edit", mpn_rev)

            # Check for outdated or modified libs
            latest = instance.get('lib_latest_rev')
            used = instance.get('lib_rev_used_here')

            if not exists_bool:
                print(f"Fetching {mpn_rev} from {source_lib_path}")
                #TODO: look into replacing this with pull_file_from_lib()
                shutil.copytree(source_lib_path, target_directory)
                used = latest
                print(f"File {mpn_rev} added to {target_directory}")

            if int(latest) > int(used):
                print(f"There's a newer revision available. If you want to update, delete {mpn_rev} from library_used.")
            elif int(latest) < int(used):
                print("Somehow you've imported a revision that's newer than what's in the library. You goin crazy!")
                exit()
            else:
                if find_modifications(source_lib_path, target_directory) == False:
                    print("Library is up to date.")
                else:
                    raise RuntimeError(
                        "Either you've modified the library as-imported (not allowed for traceability purposes) or the library has changed without adding a new rev. Either choose a different rev or delete the libraries used from the part to re-import."
                    )

            copy_in_editable_file(instance.get('instance_name'))

        else:
            print(f"Libraries for component type '{instance.get('item_type')}' either not needed or not supported")

        updated_instances.append(instance)

        #TODO: combine these two?
        #remember which files are supposed to exist so we can later delete invalid stuff
        add_filename_to_drawing_instance_list(instance.get('instance_name'))

        print()

    # Write all modified rows back at once
    fieldnames = updated_instances[0].keys()
    with open(fileio.path("instances list"), "w", newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter='\t')
        writer.writeheader()
        writer.writerows(updated_instances)  

def copy_in_editable_file(instance_name):
    # Patterns to match → new filename template (case-sensitive)
    patterns = [
        (re.compile(r'.*-attributes\.json$'), f"{instance_name}-attributes.json"),
        (re.compile(r'.*-drawing\.svg$'), f"{instance_name}-drawing.svg"),
    ]

    """
    For a given instance_name, copies editable files from:
    drawing_instances/<instance_name>/library_used_do_not_edit/<mpn-rev>/
    to:
    drawing_instances/<instance_name>/

    Files copied:
      *-attributes.json → <instance_name>-attributes.json
      *-drawing.svg     → <instance_name>-drawing.svg

    Only copies if the destination file does not already exist.

    Returns:
        A list of dicts: [{source_filename: ..., destination_filename: ...}, ...]
    """
    copied_files = []

    base_dir = fileio.dirpath("editable_component_data")
    src_root = os.path.join(base_dir, instance_name, "library_used_do_not_edit")
    dst_dir = os.path.join(base_dir, instance_name)

    # Validate exactly one subfolder (mpn-rev)
    try:
        subfolders = [name for name in os.listdir(src_root)
                      if os.path.isdir(os.path.join(src_root, name))]
    except FileNotFoundError:
        return copied_files  # library_used_do_not_edit does not exist

    if len(subfolders) != 1:
        raise RuntimeError(f"Expected exactly one mpn-rev folder in {src_root}, found: {subfolders}")

    mpn_rev_folder = subfolders[0]
    src_dir = os.path.join(src_root, mpn_rev_folder)

    for filename in os.listdir(src_dir):
        src_file = os.path.join(src_dir, filename)

        if not os.path.isfile(src_file):
            continue

        for pattern, dest_name in patterns:
            if pattern.match(filename):
                dst_file = os.path.join(dst_dir, dest_name)
                if not os.path.exists(dst_file):
                    shutil.copy2(src_file, dst_file)
                    copied_files.append({
                        "source_filename": src_file,
                        "destination_filename": dst_file
                    })
                    print(f"Editable file {os.path.basename(dst_file)} copied to instance folder.")
                else:
                    print(f"Editable file {os.path.basename(dst_file)} left unchanged within its instance folder")
                break
    return copied_files

def exists_in_lib_used(instance_name, mpn):
    # Look for revision folders inside library_used/<instance_name>/
    base_path = os.path.join(fileio.dirpath("editable_component_data"), instance_name, "library_used_do_not_edit")

    try:
        for name in os.listdir(base_path):
            full_path = os.path.join(base_path, name)
            if os.path.isdir(full_path) and name.startswith(mpn):
                match = re.search(r'rev(\d+)', name, re.IGNORECASE)
                if match:
                    return True, match.group(1)
    except FileNotFoundError:
        return False, ""

    return False, ""

pn = None
rev = None

def generate_new_connector_template():
    global pn, rev
    pn = harnice_prechecker.pn_from_cwd()
    rev = harnice_prechecker.rev_from_cwd()

    if(harnice_prechecker.harnice_prechecker() == False):
        return

    #make_new_part_svg()
    make_new_part_json()

def make_new_part_json():
    attributes_blank_json = {
        "plotting_info": {
            "csys_parent_prefs": [
                ".node"
            ],
            "component_translate_inches": {
                "translate_x": 0,
                "translate_y": 0,
                "rotate_csys": 0
            }
        },
        "tooling_info": {
            "tools": []
        },
        "build_notes": [],
        "flagnote_locations": [
            {"angle": 0, "distance": 2},
            {"angle": 15, "distance": 2},
            {"angle": -15, "distance": 2},
            {"angle": 30, "distance": 2},
            {"angle": -30, "distance": 2},
            {"angle": 45, "distance": 2},
            {"angle": -45, "distance": 2},
            {"angle": 60, "distance": 2},
            {"angle": -60, "distance": 2}
        ]
    }

    attributes_blank_json_path = os.path.join(os.getcwd(), f"{pn}-attributes.json")

    if os.path.exists(attributes_blank_json_path):
        os.remove(attributes_blank_json_path)

    # Write new file
    with open(attributes_blank_json_path, "w") as json_file:
        json.dump(attributes_blank_json, json_file, indent=4)

# Function to create the root SVG element
#def make_new_part_svg():
    #create_svg()
    #add_defs()
    #add_named_view()
    #add_content()
    #save_svg()

def create_svg(width=500, height=500):
    svg = ET.Element("svg", {
        "version": "1.1",
        "id": "svg1",
        "xmlns": "http://www.w3.org/2000/svg",
        "xmlns:svg": "http://www.w3.org/2000/svg",
        "xmlns:inkscape": "http://www.inkscape.org/namespaces/inkscape",
        "xmlns:sodipodi": "http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd"
    })
    return svg

# Function to add a defs section with a rectangle and marker
def add_defs(svg):
    defs = ET.SubElement(svg, "defs", {"id": "defs1"})

    # Add rectangle
    ET.SubElement(defs, "rect", {
        "x": "197.53245",
        "y": "17.037839",
        "width": "138.96487",
        "height": "107.55136",
        "id": "rect1"
    })

    # Add marker
    marker = ET.SubElement(defs, "marker", {
        "style": "overflow:visible",
        "id": "ConcaveTriangle-80",
        "refX": "0",
        "refY": "0",
        "orient": "auto-start-reverse",
        "markerWidth": "1",
        "markerHeight": "1",
        "viewBox": "0 0 1 1"
    })
    ET.SubElement(marker, "path", {
        "transform": "scale(0.7)",
        "d": "M -2,-4 9,0 -2,4 c 2,-2.33 2,-5.66 0,-8 z",
        "style": "fill:context-stroke;fill-rule:evenodd;stroke:none",
        "id": "path7-4"
    })

# Function to add a named view
def add_named_view(svg):
    ET.SubElement(svg, "sodipodi:namedview", {
        "id": "namedview1",
        "pagecolor": "#ffffff",
        "bordercolor": "#000000",
        "borderopacity": "0.25",
        "inkscape:showpageshadow": "2",
        "inkscape:pageopacity": "0.0",
        "inkscape:deskcolor": "#d1d1d1",
    })

# Function to add content groups with parametrized buildnotes
def add_content(svg, default_bubble_locs):
    contents = ET.SubElement(svg, "g", {"id": "connector-drawing-contents-start"})

    drawing_group = ET.SubElement(contents, "g", {"id": "connector-drawing"})
    add_drawing = ET.SubElement(drawing_group, "g", {"id": "add-drawing-here"})

    # Add placeholder circle
    ET.SubElement(add_drawing, "circle", {
        "style": "fill:#000000;stroke:#000000;stroke-width:0.015;stroke-dasharray:0.18, 0.18",
        "id": "path1",
        "cx": "0",
        "cy": "0",
        "r": "10",
        "inkscape:label": "placeholder-deleteme"
    })

    contents = ET.SubElement(svg, "g", {"id": "connector-drawing-contents-end"})

# Function to save the SVG to a file
def save_svg(svg, filename):
    tree = ET.ElementTree(svg)
    # Convert the ElementTree to a string
    rough_string = ET.tostring(tree.getroot(), encoding="UTF-8")
    # Parse the string into a DOM object
    parsed = xml.dom.minidom.parseString(rough_string)
    # Pretty-print the DOM object
    pretty_svg = parsed.toprettyxml(indent="  ")
    # Write the formatted SVG to a file
    with open(filename, "w", encoding="UTF-8") as file:
        file.write(pretty_svg)

def latest_version_in_lib(domain, library_subpath, lib_name):
    """
        find the rev history tsv in the component lib
        open it
        find the row with the highest rev number
    return latest_rev_in_lib
    """

def rev_in_lib_used(domain, library_subpath, lib_name):
    """
        rev_in_lib_used = 
        is there a fileio function that returns the rev number of a directory?
        find the rev number of the directory in the library_used directory
    """

def detect_modified_files(domain, library_subpath, lib_name):
    """
    is_a_match = 
        compare all files in the library_used directory to the files in the component lib
        if all files match, return True
        if any file does not match, return False
    """
def find_modifications(dir1, dir2):
    # Perform a recursive comparison
    dir_comparison = filecmp.dircmp(dir1, dir2)

    # Check for any differences in files or subdirectories
    if dir_comparison.left_only or dir_comparison.right_only or dir_comparison.funny_files:
        return True

    (match, mismatch, errors) = filecmp.cmpfiles(
        dir1, dir2, dir_comparison.common_files, shallow=False
    )
    if mismatch or errors:
        return True

    # Recursively check subdirectories
    for subdir in dir_comparison.common_dirs:
        subdir1 = os.path.join(dir1, subdir)
        subdir2 = os.path.join(dir2, subdir)
        if detect_modified_files(subdir1, subdir2):
            return True

    return False

def add_filename_to_drawing_instance_list(filename):
    global drawing_instance_filenames  # Declare the global variable
    if drawing_instance_filenames == [None]:  # Replace initial None with the first item
        drawing_instance_filenames = [filename]
    else:
        drawing_instance_filenames.append(filename)  # Append new filename

def delete_unmatched_files():
    global drawing_instance_filenames  # Access the global variable

    # List all files and directories in the directory
    for item in os.listdir(fileio.dirpath("editable_component_data")):
        item_path = os.path.join(fileio.dirpath("editable_component_data"), item)

        # Check if the item is not in the allowed list
        if item not in drawing_instance_filenames:
            # Check if it's a file
            if os.path.isfile(item_path):
                try:
                    os.remove(item_path)  # Delete the file
                    print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Deleted unmatching file: {basename(item_path)} in 'drawing instances'")
                except Exception as e:
                    print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Error deleting unmatching file: {basename(item_path)} in 'drawing instances': {e}")

            # Check if it's a directory
            elif os.path.isdir(item_path):
                try:
                    shutil.rmtree(item_path)  # Delete the directory and its contents
                    print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Deleted unmatching directory: {basename(item_path)} in 'drawing instances'")
                except Exception as e:
                    print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Error deleting unmatching directory: {basename(item_path)} in 'drawing instances': {e}")
      
def copy_svg_data(instance_name):
    svg_path = os.path.join(
        fileio.dirpath("editable_component_data"),
        instance_name,
        f"{instance_name}-drawing.svg"
    )

    if not os.path.exists(svg_path):
        raise FileNotFoundError(f"SVG file not found: {svg_path}")

    with open(svg_path, 'r') as f:
        contents = f.read()

    # Extract contents between <svg> and </svg>
    match = re.search(r"<svg[^>]*>(.*?)</svg>", contents, flags=re.DOTALL)
    if not match:
        raise ValueError(f"No valid <svg> content in {svg_path}")

    return match.group(1).strip()
    
def pull_file_from_lib(domain, lib_file, destination_filepath, remove_ok=True):
    load_dotenv()

    # Step 1: Check the source file
    source_filepath = os.path.join(os.getenv(domain), lib_file)
    if not os.path.isfile(source_filepath):
        raise FileNotFoundError(f"Specified titleblock not found in library: {source_filepath}")

    # Step 2: Check on the destination file
    if os.path.isfile(destination_filepath):
        if remove_ok:
            os.remove(destination_filepath)
        else:
            print(f"Importing file from library: {lib_file}. File already exists and I was told not to rewrite it.")
            return

    # Step 3: Copy directly to destination
    shutil.copy(source_filepath, destination_filepath)

def make_new_tblock(filename):
    # === Parameters ===
    page_size = [11 * 96, 8.5 * 96]
    outer_margin = 20
    inner_margin = 40
    tick_spacing = 96
    tb_origin_offset = (398, 48)
    row_heights = [24, 24]
    column_widths = [
        [264, 50, 84],
        [73, 126, 139, 60]
    ]
    label_offset = (2, 7)
    key_offset_y = 16
    cell_texts = [
        [("DESCRIPTION", "tblock-key-desc"), ("REV", "tblock-key-rev"), ("RELEASE TICKET", "tblock-key-releaseticket")],
        [("SCALE", "tblock-key-scale"), ("PART NUMBER", "tblock-key-pn"),
         ("DRAWN BY", "tblock-key-drawnby"), ("SHEET", "tblock-key-sheet")]
    ]

    width, height = page_size
    svg = ET.Element('svg', {
        "xmlns": "http://www.w3.org/2000/svg",
        "version": "1.1",
        "width": str(width),
        "height": str(height)
    })

    contents_group = ET.SubElement(svg, "g", {"id": "tblock-contents-start"})

    def add_rect(parent, x, y, w, h, stroke="black", fill="none", stroke_width=1):
        ET.SubElement(parent, "rect", {
            "x": str(x),
            "y": str(y),
            "width": str(w),
            "height": str(h),
            "fill": fill,
            "stroke": stroke,
            "stroke-width": str(stroke_width)
        })

    def add_text(parent, x, y, text, size=8, anchor="start", bold=False, id=None):
        style = f"font-size:{size}px;font-family:Arial"
        if bold:
            style += ";font-weight:bold"
        attrs = {
            "x": str(x),
            "y": str(y),
            "style": style,
            "text-anchor": anchor,
        }
        if id:
            attrs["id"] = id
        ET.SubElement(parent, "text", attrs).text = text

    # === Border Group ===
    border_group = ET.SubElement(contents_group, "g", {"id": "border"})

    x_ticks = int((width - 2 * inner_margin) // tick_spacing)
    for i in range(x_ticks):
        x0 = inner_margin + i * tick_spacing
        x1 = x0 + tick_spacing
        x_center = (x0 + x1) / 2

        ET.SubElement(border_group, "line", {
            "x1": str(x0), "y1": str(outer_margin),
            "x2": str(x0), "y2": str(height - outer_margin),
            "stroke": "black", "stroke-width": "0.5"
        })

        label_y_top = (outer_margin + inner_margin) / 2
        label_y_bot = height - label_y_top
        add_text(border_group, x_center, label_y_top, str(i + 1), anchor="middle")
        add_text(border_group, x_center, label_y_bot, str(i + 1), anchor="middle")

    x_end = inner_margin + x_ticks * tick_spacing
    ET.SubElement(border_group, "line", {
        "x1": str(x_end), "y1": str(outer_margin),
        "x2": str(x_end), "y2": str(height - outer_margin),
        "stroke": "black", "stroke-width": "0.5"
    })

    y_ticks = int((height - 2 * inner_margin) // tick_spacing)
    for j in range(y_ticks):
        y0 = inner_margin + j * tick_spacing
        y1 = y0 + tick_spacing
        y_center = (y0 + y1) / 2

        ET.SubElement(border_group, "line", {
            "x1": str(outer_margin), "y1": str(y0),
            "x2": str(width - outer_margin), "y2": str(y0),
            "stroke": "black", "stroke-width": "0.5"
        })

        label = chr(ord('A') + j)
        label_x_left = (outer_margin + inner_margin) / 2
        label_x_right = width - label_x_left
        add_text(border_group, label_x_left, y_center + 4, label, anchor="middle")
        add_text(border_group, label_x_right, y_center + 4, label, anchor="middle")

    y_end = inner_margin + y_ticks * tick_spacing
    ET.SubElement(border_group, "line", {
        "x1": str(outer_margin), "y1": str(y_end),
        "x2": str(width - outer_margin), "y2": str(y_end),
        "stroke": "black", "stroke-width": "0.5"
    })

    add_rect(border_group, outer_margin, outer_margin, width - 2 * outer_margin, height - 2 * outer_margin)
    add_rect(border_group, inner_margin, inner_margin,
             width - 2 * inner_margin, height - 2 * inner_margin,
             stroke="black", fill="white", stroke_width=1)

    # === Logo Group ===
    tb_origin_x = width - inner_margin - tb_origin_offset[0]
    tb_origin_y = height - inner_margin - tb_origin_offset[1]
    logo_width = 1.25 * 96
    logo_height = sum(row_heights)
    logo_group = ET.SubElement(contents_group, "g", {"id": "logo"})
    add_rect(logo_group,
             tb_origin_x - logo_width,
             tb_origin_y,
             logo_width,
             logo_height,
             stroke="black", fill="none")

    # === Titleblock Cell Groups ===
    y_cursor = tb_origin_y
    for row_idx, row_height in enumerate(row_heights):
        row_cols = column_widths[row_idx]
        row_cells = cell_texts[row_idx]
        x_cursor = tb_origin_x
        for col_idx, col_width in enumerate(row_cols):
            label, key_id = row_cells[col_idx]
            group_id = label.lower().replace(" ", "-") if label else f"cell-r{row_idx}-c{col_idx}"
            cell_group = ET.SubElement(contents_group, "g", {"id": group_id})
            add_rect(cell_group, x_cursor, y_cursor, col_width, row_height)

            if label:
                add_text(cell_group,
                         x_cursor + label_offset[0],
                         y_cursor + label_offset[1],
                         label, size=7, bold=True)
            if key_id:
                center_x = x_cursor + col_width / 2
                add_text(cell_group,
                         center_x,
                         y_cursor + key_offset_y,
                         key_id, size=7, anchor="middle", id=key_id)

            x_cursor += col_width
        y_cursor += row_height

    # === Write SVG with indentation ===
    ET.SubElement(svg, "g", {"id": "tblock-contents-end"})
    rough_string = ET.tostring(svg, encoding="utf-8")
    pretty = minidom.parseString(rough_string).toprettyxml(indent="  ")
    with open(os.path.join(os.getcwd(), filename), "w", encoding="utf-8") as f:
        f.write(pretty)