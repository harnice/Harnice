import os
#from os.path import basename, dirname
#import json
#import shutil
#import xml.etree.ElementTree as ET
#from os.path import basename, dirname
#from inspect import currentframe
#import yaml
#import csv
import math
#from flagnote_functions import update_flagnotes_of_instance, apply_bubble_transforms_to_flagnote_group
#import fileio
#import component_library
import instances_list

import svg_utils
import fileio
from collections import defaultdict

import os
from collections import defaultdict
import component_library

def make_new_formboard_master_svg():
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
        content_lines.append(f'    <g id="{item_type}">')
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
            content_lines.append(f'      <g transform="translate({px_x},{px_y}) rotate({angle})">'
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
    print("!!!!!!!")
    print(f"{instance_name}: {x_pos}, {y_pos}, {angle}")
    return x_pos, y_pos, angle

def update_segment_instances():
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

                half_length = length / 2
                half_diameter = diameter / 2

                svg_content = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{length}" height="{diameter}" viewBox="{-half_length} {-half_diameter} {length} {diameter}">
    <line x1="{-half_length}" y1="0" x2="{half_length}" y2="0" stroke="black" stroke-width="{diameter}" />
    <line x1="{-half_length}" y1="0" x2="{half_length}" y2="0" stroke="white" stroke-width="{diameter - outline_thickness}" />
    <line x1="{-half_length}" y1="0" x2="{half_length}" y2="0" stroke="black" style="stroke-width:{centerline_thickness};stroke-dasharray:18,18;stroke-dashoffset:0" />
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


"""
def update_bom_instance(instance_name, mpn, supplier, bomid, instance_type, rotation, offset):
    #create an svg for that instance

    #update the instance name
    instance_name_w_suffix = instance_name
    if(instance_type == "Backshell"):
        instance_name_w_suffix = f"{instance_name}.bs"

    print(f"#    #    ########## working on bom item {mpn}, instance name {instance_name_w_suffix}, which is type {instance_type}")

    instance_fileio.dirpath = os.path.join(fileio.dirpath("editable_component_data"),instance_name_w_suffix)

    #import from library
    svgexists = component_library.import_library_file(supplier,os.path.join("component_definitions",mpn),f"{mpn}-drawing.svg")
    jsonsuccessfulimport = component_library.import_library_file(supplier,os.path.join("component_definitions",mpn),f"{mpn}-attributes.json")

    if svgexists:
        #reference the drawing filepath, not included in fileio.path() because each project file structure is different
        instance_svg_path = os.path.join(instance_fileio.dirpath, f"{fileio.partnumber("pn-rev")}-{instance_name_w_suffix}.svg")

        #create a new instance file if it doesn't exist yet
        if not os.path.exists(instance_svg_path):
            print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Generating  instance svg {fileio.partnumber("pn-rev")}-{instance_name_w_suffix}.svg")
            os.makedirs(instance_fileio.dirpath, exist_ok=True)

            # Write SVG declaration
            svg_content = '<svg xmlns="http://www.w3.org/2000/svg"></svg>'

            with open(instance_svg_path, 'w') as blank_svg:
               blank_svg.write(svg_content)

            # Verify the file content
            with open(instance_svg_path, 'r') as verify_svg:
                content = verify_svg.read()

            print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Created new connector instance SVG {instance_name_w_suffix} with MPN: {mpn}")

            svg_utils.add_entire_svg_file_contents_to_group(instance_svg_path,"connector-drawing")
            svg_utils.find_and_replace_svg_group(instance_svg_path, os.path.join(fileio.dirpath("editable_component_data"), "component_definitions", mpn, f"{mpn}-drawing.svg"), "connector-drawing")
            svg_utils.add_entire_svg_file_contents_to_group(instance_svg_path, "connector-instance-rotatables")
            svg_utils.add_entire_svg_file_contents_to_group(instance_svg_path, f"unique-instance-{instance_name_w_suffix}")
            apply_bubble_transforms_to_flagnote_group(instance_svg_path)
                        
        else: 
            print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Preserving existing contents of {instance_name_w_suffix} instance file. ")
      
        # Rotate SVG group "connector-drawing" to match the average segment angle
        connector_angle = -1* retrieve_angle_of_connector(instance_name)
        svg_utils.rotate_svg_group(instance_svg_path, "connector-instance-rotatables", connector_angle)
        #TODO: offset and rotate per rotation and offset arguents of this function
        update_flagnotes_of_instance(os.path.dirname(instance_svg_path), instance_name_w_suffix, connector_angle, bomid)

def update_formboard_master_svg():
    # Create the root SVG element
    svg = ET.Element("svg", xmlns="http://www.w3.org/2000/svg", version="1.1")

    with open(fileio.path("formboard segment to from center"), 'r') as json_file:
        segment_locations = json.load(json_file)
    '''
    for segment in segment_locations:

        segment_name = segment["segment name"]
        group = ET.SubElement(svg, "g", id=segment_name)
        center_coordinates = segment["center"]["coordinates"]
        
        center_x, center_y = center_coordinates

        translation = [96* center_x, 96*center_y]
        translation[1] = -translation[1]
        group.set("transform", f"translate({translation[0]}, {translation[1]}) scale(1)")
        
        # Add contents start and end groups
        ET.SubElement(group, "g", id=f"unique-instance-{segment_name}-contents-start")
        ET.SubElement(group, "g", id=f"unique-instance-{segment_name}-contents-end")'''
    
    #Store the list of instances getting groups into instances[]
    instances = []
    with open(fileio.path("instances list"), mode="r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file, delimiter="\t")  # Read TSV with tab delimiter
        for row in reader:
            instances.append(row["instance name"])
    
    # Read the node locations JSON file
    with open(fileio.path("formboard node locations px"), 'r') as json_file:
        node_locations = json.load(json_file)

    # Add groups for each connector with transformations
    instance_counter = 0
    for each in instances:
        instance_name = instances[instance_counter]
        instance_counter += 1
        group = ET.SubElement(svg, "g", id=instance_name)
        
        # Apply translation and scale
        translation = node_locations.get(instance_name, [0, 0])
        translation[1] = -translation[1]
        group.set("transform", f"translate({translation[0]}, {translation[1]}) scale(1)")
        
        # Add contents start and end groups
        ET.SubElement(group, "g", id=f"unique-instance-{instance_name}-contents-start")
        ET.SubElement(group, "g", id=f"unique-instance-{instance_name}-contents-end")

    # Write the SVG to file with proper formatting and newlines
    with open(fileio.path("formboard master svg"), 'w', encoding='utf-8') as svg_file:
        svg_file.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        svg_file.write('<svg xmlns="http://www.w3.org/2000/svg" version="1.1">\n')
        for group in svg:
            svg_file.write(f'  {ET.tostring(group, encoding="unicode").strip()}\n\n')
        svg_file.write('</svg>\n')

    svg_utils.add_entire_svg_file_contents_to_group(fileio.path("formboard master svg"),"formboard-master")
    
    #Replace all connector groups in the target SVG with their corresponding source SVG groups
    instance_counter = 0
    for each in instances:
        instance_name = instances[instance_counter]
        instance_counter += 1
        # find the path of the source instance
        source_svg_filepath = os.path.join(fileio.dirpath("editable_component_data"), instance_name, f"{fileio.partnumber("pn-rev")}-{instance_name}.svg")
        
        # Call the function to replace the group
        svg_utils.find_and_replace_svg_group(fileio.path("formboard master svg"), source_svg_filepath, f"unique-instance-{instance_name}")

def replace_all_segment_groups():
    #Replace all segment groups in the target SVG with their corresponding source SVG groups.
    # Load the segment data JSON
    try:
        with open(fileio.path("formboard segment to from center"), 'r') as json_file:
            segment_data = json.load(json_file)
    except FileNotFoundError:
        print(f"Error: Segment data JSON file {fileio.name("formboard segment to from center")} not found.")
        return
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return

    # Loop through each segment and replace the corresponding group
    for segment in segment_data:
        segment_name = segment.get("segment name")
        if not segment_name:
            print("Skipping segment with missing 'segment name'.")
            continue

        try:
            # Define the target and source SVG paths
            source_svg_filepath = os.path.join(fileio.dirpath("editable_component_data"), segment_name, f"{fileio.partnumber("pn-rev")}-{segment_name}.svg")

            if not os.path.exists(fileio.path("formboard master svg")):
                print(f"Error: Target SVG file {fileio.path("formboard master svg")} not found.")
                continue

            if not os.path.exists(source_svg_filepath):
                print(f"Error: Source SVG file {source_svg_filepath} not found.")
                continue

            # Call the function to replace the group
            svg_utils.find_and_replace_svg_group(fileio.path("formboard master svg"), source_svg_filepath, f"unique-instance-{segment_name}")

            print(f"Successfully replaced group for segment {segment_name}.")
        except Exception as e:
            print(f"Error processing segment {segment_name}: {e}")

def retrieve_angle_of_connector(connectorname):
    #Retrieve the angle of the specified connector from the JSON file.
    
    with open(fileio.path("formboard node locations inches"), "r") as file:
        data = json.load(file)
    
    # Retrieve the angle for the specified connector
    try:
        angle = data[connectorname]["angle"]
    except KeyError:
        raise KeyError(f"Connector '{connectorname}' not found in the JSON data.")
    
    return angle

def retrieve_angle_of_segment(segmentname):

    # Check if the file exists
    if not os.path.isfile(fileio.path("formboard graph definition")):
        raise FileNotFoundError(f"File not found: {fileio.name("formboard graph definition")}")
    
    # Load the JSON data
    with open(fileio.path("formboard graph definition"), "r") as file:
        data = json.load(file)
    
    # Retrieve the angle for the specified connector
    try:
        angle = data[segmentname]["angle"]
    except KeyError:
        raise KeyError(f"Segment '{segmentname}' not found in the JSON data.")
    
    return angle
"""