import os
from os.path import basename, dirname
import json
import shutil
import xml.etree.ElementTree as ET
from os.path import basename, dirname
from inspect import currentframe
import yaml  # PyYAML for parsing YAML files
from flagnote_functions import update_flagnotes_of_instance, apply_bubble_transforms_to_flagnote_group
from utility import *

#this list is used to keep track of all the valid instances:
drawing_instance_filenames = [None]
#when creating new instances, add to this list by add_filename_to_drawing_instance_list().
#directories in drawing-instances that are not named in this list will be deleted by delete_unmatched_files().

def add_filename_to_drawing_instance_list(filename):
    global drawing_instance_filenames  # Declare the global variable
    if drawing_instance_filenames == [None]:  # Replace initial None with the first item
        drawing_instance_filenames = [filename]
    else:
        drawing_instance_filenames.append(filename)  # Append new filename

def delete_unmatched_files():
    global drawing_instance_filenames  # Access the global variable

    # Ensure the directory exists
    if not os.path.exists(dirpath("drawing-instances")):
        print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Directory {dirpath("drawing-instances")} does not exist.")
        return

    # List all files and directories in the directory
    for item in os.listdir(dirpath("drawing-instances")):
        item_path = os.path.join(dirpath("drawing-instances"), item)

        # Check if the item is not in the allowed list
        if item not in drawing_instance_filenames:
            # Check if it's a file
            if os.path.isfile(item_path):
                try:
                    os.remove(item_path)  # Delete the file
                    print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Deleted unmatching file: {basename(item_path)} in 'drawing-instances'")
                except Exception as e:
                    print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Error deleting unmatching file: {basename(item_path)} in 'drawing-instances': {e}")

            # Check if it's a directory
            elif os.path.isdir(item_path):
                try:
                    shutil.rmtree(item_path)  # Delete the directory and its contents
                    print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Deleted unmatching directory: {basename(item_path)} in 'drawing-instances'")
                except Exception as e:
                    print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Error deleting unmatching directory: {basename(item_path)} in 'drawing-instances': {e}")

def update_all_bom_instances():
    #Go through the harness bom and call update_bom_instance slightly differently depending on small details
    #bom instances account for every item except segments

    with open(filepath("harness bom"), 'r') as bom_file:
        # Read the header line first
        header_line = bom_file.readline()
        header = header_line.strip().split("\t")
        
        # Identify indices from the header
        id_index = header.index("Id")
        mpn_index = header.index("MPN")
        desc_simple_index = header.index("Description Simple")
        supplier_index = header.index("Supplier")

        # Read the remaining data (if needed)
        bom_data = bom_file.read()
        bom_lines = bom_data.splitlines()

    # Load YAML file
    with open(filepath("wireviz yaml"), 'r') as yaml_file:
        yaml_data = yaml.safe_load(yaml_file)

    #for each line in harness bom:
    for line in bom_lines:

        columns = line.strip().split("\t")
        current_desc_simple = columns[desc_simple_index]

        #if "Description Simple" == "Backshell" in harness bom (do this first because it informs rotation of others)
        if current_desc_simple == "Backshell":
            current_mpn = columns[mpn_index]

            #for each connector in yaml
            for connector_name, connector in yaml_data.get("connectors", {}).items():
                # Check if any additional component is a Backshell with mpn equal to current_mpn
                if any(
                    component.get("type") == "Backshell" and component.get("mpn") == current_mpn
                    for component in connector.get("additional_components", [])
                ):
                    backshelldrivenrotation = 0
                    backshelldrivenoffset = 0
                    update_bom_instance(f"{connector_name}", current_mpn, columns[supplier_index], columns[id_index], current_desc_simple, backshelldrivenrotation, backshelldrivenoffset)
                    

        if current_desc_simple == "Connector":
            current_mpn = columns[mpn_index]  

            #for each connector in yaml
            for connector_name, connector in yaml_data.get("connectors", {}).items():
                #if "mpn" in yaml == "MPN" in harness bom
                if connector.get("mpn") == current_mpn:

                    #if connector has any backshell as an additional part
                    if any(
                        component.get("type") == "Backshell" for 
                        component in connector.get("additional_components", [])
                    ):
                        #TODO look up the rotations from that backshell's json definition
                        backshelldrivenrotation = 0
                        backshelldrivenoffset = 0
                    
                update_bom_instance(f"{connector_name}", current_mpn, columns[supplier_index], columns[id_index], current_desc_simple, backshelldrivenrotation, backshelldrivenoffset)
                
def update_bom_instance(instance_name, mpn, supplier, bomid, instance_type, rotation, offset):
    #create an svg for that instance

    #update the instance name
    instance_name_w_suffix = instance_name
    if(instance_type == "Backshell"):
        instance_name_w_suffix = f"{instance_name}.bs"

    print(f"#    #    ########## working on bom item {mpn}, instance name {instance_name_w_suffix}, which is type {instance_type}")
    
    #make sure the main directory of all drawing instances is there
    os.makedirs(dirpath("drawing-instances"), exist_ok=True)

    #make sure this particular instance directory is there
    os.makedirs(os.path.join(dirpath("drawing-instances"),instance_name_w_suffix), exist_ok=True)
    instance_dirpath = os.path.join(dirpath("drawing-instances"),instance_name_w_suffix)

    #import from library
    svgexists = import_file_from_harnice_library(supplier,os.path.join("component_definitions",mpn),f"{mpn}-drawing.svg")
    jsonsuccessfulimport = import_file_from_harnice_library(supplier,os.path.join("component_definitions",mpn),f"{mpn}-attributes.json")
    
    #remember which files are supposed to exist so we can later delete invalid stuff
    add_filename_to_drawing_instance_list(instance_name_w_suffix)

    if svgexists:
        #reference the drawing filepath, not included in filepath() because each project file structure is different
        instance_svg_path = os.path.join(instance_dirpath, f"{partnumber("pn-rev")}-{instance_name_w_suffix}.svg")

        #create a new instance file if it doesn't exist yet
        if not os.path.exists(instance_svg_path):
            print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Generating  instance svg {partnumber("pn-rev")}-{instance_name_w_suffix}.svg")
            os.makedirs(instance_dirpath, exist_ok=True)

            # Write SVG declaration
            svg_content = '<svg xmlns="http://www.w3.org/2000/svg"></svg>'

            with open(instance_svg_path, 'w') as blank_svg:
               blank_svg.write(svg_content)

            # Verify the file content
            with open(instance_svg_path, 'r') as verify_svg:
                content = verify_svg.read()

            print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Created new connector instance SVG {instance_name_w_suffix} with MPN: {mpn}")

            add_entire_svg_file_contents_to_group(instance_svg_path,"connector-drawing")
            find_and_replace_svg_group(instance_svg_path, os.path.join(dirpath("library_used"), "component_definitions", mpn, f"{mpn}-drawing.svg"), "connector-drawing")
            add_entire_svg_file_contents_to_group(instance_svg_path, "connector-instance-rotatables")
            add_entire_svg_file_contents_to_group(instance_svg_path, f"unique-connector-instance-{instance_name_w_suffix}")
            apply_bubble_transforms_to_flagnote_group(instance_svg_path)
                        
        else: 
            print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Preserving existing contents of {instance_name_w_suffix} instance file. ")
      
        # Rotate SVG group "connector-drawing" to match the average segment angle
        connector_angle = -1* retrieve_angle_of_connector(instance_name)
        rotate_svg_group(instance_svg_path, "connector-instance-rotatables", connector_angle)
        #TODO: offset and rotate per rotation and offset arguents of this function
        update_flagnotes_of_instance(os.path.dirname(instance_svg_path), instance_name_w_suffix, connector_angle, bomid)

def update_segment_instances():
    #create SVGs for segments (instances that are not in the bom)
    try:
        with open(filepath("formboard graph definition"), 'r') as json_file:
            graph_data = json.load(json_file)
    except FileNotFoundError:
        print(f"Error: File {filename("formboard graph definition")} not found.")
        return
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return

    os.makedirs(os.path.dirname(os.path.join(os.getcwd(),"drawing-instances")), exist_ok=True)

    # Iterate through each segment in the JSON
    for segment_name, segment_data in graph_data.items():
        try:
            # Extract segment details
            length = 96* segment_data.get("length", 0)
            diameter = 96* segment_data.get("diameter", 1)  # Default to 1 if diameter is not specified

            outline_line_thickness = 0.05 * 96
            centerline_line_thickness = 0.015 * 96
            
            # Calculate SVG dimensions
            half_length = length / 2
            half_diameter = diameter / 2

            # Generate SVG content
            svg_content = f'''
    <svg xmlns="http://www.w3.org/2000/svg" width="{length}" height="{diameter}" viewBox="{-half_length} {-half_diameter} {length} {diameter}">
    <line x1="{-half_length}" y1="0" x2="{half_length}" y2="0" stroke="black" stroke-width="{diameter}" />
    <line x1="{-half_length}" y1="0" x2="{half_length}" y2="0" stroke="white" stroke-width="{diameter-outline_line_thickness}" />
    <line x1="{-half_length}" y1="0" x2="{half_length}" y2="0" stroke="black" style="stroke-width:{centerline_line_thickness};stroke-dasharray:18,18;stroke-dashoffset:0"/>
    </svg>'''

            # Define output filename
            os.makedirs(os.path.join(dirpath("drawing-instances"), segment_name), exist_ok=True)

            output_filename = os.path.join(dirpath("drawing-instances"), segment_name, f"{partnumber("pn-rev")}-{segment_name}.svg")
            
            # Write SVG file
            with open(output_filename, 'w') as svg_file:
                svg_file.write(svg_content)

            add_filename_to_drawing_instance_list(basename(dirname(output_filename)))

            add_entire_svg_file_contents_to_group(output_filename, "segment_contents_rotatables")

            rotate_svg_group(output_filename, "segment_contents_rotatables", -1*retrieve_angle_of_segment(segment_name))

            add_entire_svg_file_contents_to_group(output_filename, f"unique-segment-instance-{segment_name}")
            
            print(f"Generated SVG for {segment_name}: {output_filename}")
        
        except Exception as e:
            print(f"Error processing segment {segment_name}: {e}")

def update_formboard_master_svg():
    #TODO: clean up directory pointers
    current_dir = os.getcwd()
    node_locations_path = os.path.join(current_dir, "support-do-not-edit", "formboard_data", f"{partnumber("pn-rev")}-formboard-node-locations-px.json")
    output_svg_path = os.path.join(current_dir, "support-do-not-edit", "master-svgs", f"{partnumber("pn-rev")}-formboard-master.svg")
    segment_locations_path = os.path.join(current_dir, "support-do-not-edit", "formboard_data", f"{partnumber("pn-rev")}-formboard-segment-to-from-center.json")

    #TODO: this should rely on harness bom, not yaml
    # Read the YAML file
    with open(filepath("wireviz yaml"), 'r') as yaml_file:
        yaml_data = yaml.safe_load(yaml_file)
    
    # Read the node locations JSON file
    with open(node_locations_path, 'r') as json_file:
        node_locations = json.load(json_file)

    with open(segment_locations_path, 'r') as json_file:
        segment_locations = json.load(json_file)
    
    # Extract connectors
    connectors = yaml_data.get("connectors", {})
    
    # Create the root SVG element
    svg = ET.Element("svg", xmlns="http://www.w3.org/2000/svg", version="1.1")

    for segment in segment_locations:

        segment_name = segment["segment name"]
        group = ET.SubElement(svg, "g", id=segment_name)
        center_coordinates = segment["center"]["coordinates"]
        
        center_x, center_y = center_coordinates

        translation = [96* center_x, 96*center_y]
        translation[1] = -translation[1]
        group.set("transform", f"translate({translation[0]}, {translation[1]}) scale(1)")
        
        # Add contents start and end groups
        ET.SubElement(group, "g", id=f"unique-segment-instance-{segment_name}-contents-start")
        ET.SubElement(group, "g", id=f"unique-segment-instance-{segment_name}-contents-end")
    
    #TODO: make groups for each harness bom item
    # Add groups for each connector with transformations
    for connector_id in connectors:
        group = ET.SubElement(svg, "g", id=connector_id)
        
        # Apply translation and scale
        translation = node_locations.get(connector_id, [0, 0])
        translation[1] = -translation[1]
        group.set("transform", f"translate({translation[0]}, {translation[1]}) scale(1)")
        
        # Add contents start and end groups
        ET.SubElement(group, "g", id=f"unique-connector-instance-{connector_id}-contents-start")
        ET.SubElement(group, "g", id=f"unique-connector-instance-{connector_id}-contents-end")


    # Ensure the directory exists for the output file
    os.makedirs(os.path.dirname(output_svg_path), exist_ok=True)

    # Write the SVG to file with proper formatting and newlines
    with open(output_svg_path, 'w', encoding='utf-8') as svg_file:
        svg_file.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        svg_file.write('<svg xmlns="http://www.w3.org/2000/svg" version="1.1">\n')
        for group in svg:
            svg_file.write(f'  {ET.tostring(group, encoding="unicode").strip()}\n\n')
        svg_file.write('</svg>\n')

    add_entire_svg_file_contents_to_group(output_svg_path,"formboard-master")
    
    print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: SVG file {'overwritten' if os.path.exists(output_svg_path) else 'created'} at: {output_svg_path}")

#TODO: udpate to all instance groups
def replace_all_connector_groups():
    """Replace all connector groups in the target SVG with their corresponding source SVG groups."""
    current_dir = os.getcwd()
    formboard_graph_definition_path = os.path.join(current_dir, f"{partnumber("pn-rev")}-formboard-graph-definition.json")

    #TODO: reference the harness bom, not the yaml
    # Load the YAML file
    with open(filepath("wireviz yaml"), 'r') as yaml_file:
        yaml_data = yaml.safe_load(yaml_file)

    # Load the formboard graph definition JSON
    try:
        with open(formboard_graph_definition_path, 'r') as json_file:
            graph_data = json.load(json_file)
    except FileNotFoundError:
        print(f"Error: File {formboard_graph_definition_path} not found.")
        return
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return


    # Extract connectors from the YAML
    connectors = yaml_data.get("connectors", {})

    for connector_name in connectors:
        # Define the target and source SVG paths
        target_svg_filepath = os.path.join(current_dir, "support-do-not-edit", "master-svgs", f"{partnumber("pn-rev")}-formboard-master.svg")
        source_svg_filepath = os.path.join(current_dir, "drawing-instances", connector_name, f"{partnumber("pn-rev")}-{connector_name}.svg")
        
        # Call the function to replace the group
        find_and_replace_svg_group(target_svg_filepath, source_svg_filepath, f"unique-connector-instance-{connector_name}")

def replace_all_segment_groups():
    """Replace all segment groups in the target SVG with their corresponding source SVG groups."""
    current_dir = os.getcwd()
    segment_data_path = os.path.join(current_dir, "support-do-not-edit", "formboard_data", f"{partnumber("pn-rev")}-formboard-segment-to-from-center.json")

    # Load the segment data JSON
    try:
        with open(segment_data_path, 'r') as json_file:
            segment_data = json.load(json_file)
    except FileNotFoundError:
        print(f"Error: Segment data JSON file {segment_data_path} not found.")
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
            target_svg_filepath = os.path.join(current_dir, "support-do-not-edit", "master-svgs", f"{partnumber("pn-rev")}-formboard-master.svg")
            source_svg_filepath = os.path.join(current_dir, "drawing-instances", segment_name, f"{partnumber("pn-rev")}-{segment_name}.svg")

            if not os.path.exists(target_svg_filepath):
                print(f"Error: Target SVG file {target_svg_filepath} not found.")
                continue

            if not os.path.exists(source_svg_filepath):
                print(f"Error: Source SVG file {source_svg_filepath} not found.")
                continue

            # Call the function to replace the group
            find_and_replace_svg_group(target_svg_filepath, source_svg_filepath, f"unique-segment-instance-{segment_name}")

            print(f"Successfully replaced group for segment {segment_name}.")
        except Exception as e:
            print(f"Error processing segment {segment_name}: {e}")

def retrieve_angle_of_connector(connectorname):
    #Retrieve the angle of the specified connector from the JSON file.
    
    with open(filepath("formboard node locations inches"), "r") as file:
        data = json.load(file)
    
    # Retrieve the angle for the specified connector
    try:
        angle = data[connectorname]["angle"]
    except KeyError:
        raise KeyError(f"Connector '{connectorname}' not found in the JSON data.")
    
    return angle

def retrieve_angle_of_segment(segmentname):
    # Check if the file exists
    if not os.path.isfile(filepath("formboard graph definition")):
        raise FileNotFoundError(f"File not found: {filename("formboard graph definition")}")
    
    # Load the JSON data
    with open(filepath("formboard graph definition"), "r") as file:
        data = json.load(file)
    
    # Retrieve the angle for the specified connector
    try:
        angle = data[segmentname]["angle"]
    except KeyError:
        raise KeyError(f"Segment '{segmentname}' not found in the JSON data.")
    
    return angle

def regen_formboard():
    print("#    ############ UPDATING CONNECTOR INSTANCES ############")
    update_all_bom_instances()

    print("#    ############ UPDATING SEGMENT INSTANCES ############")
    update_segment_instances()

    print("#    ############ DELETING UNMATCHED FILES ############")
    delete_unmatched_files()

    print("#    ############ CREATING NEW FORMBOARD MASTER SVG WITH GROUP STRUCTURE ############")
    #creates an svg file with the groups in the right places
    #does not add any content because that's all done via group replacement, but nothing is created until this is done
    update_formboard_master_svg()

    print("#    ############ REPLACING ALL CONNECTOR GROUPS INTO FORMBOARD MASTER ############")
    replace_all_connector_groups()

    print("#    ############ REPLACING ALL INSTANCE GROUPS INTO FORMBOARD MASTER ############")
    replace_all_segment_groups()

if __name__ == "__main__":
    regen_formboard()