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

#used to keep track of all the valid instances. those that are not named in this array will be deleted
drawing_instance_filenames = [None]

def add_filename_to_drawing_instance_list(filename):
    global drawing_instance_filenames  # Declare the global variable
    if drawing_instance_filenames == [None]:  # Replace initial None with the first item
        drawing_instance_filenames = [filename]
    else:
        drawing_instance_filenames.append(filename)  # Append new filename

def delete_unmatched_files(directory):
    """
    Deletes all files and subdirectories in the given directory that are not in the global list `drawing_instance_filenames`.

    Args:
        directory (str): The path to the directory to clean.
    """
    global drawing_instance_filenames  # Access the global variable

    # Ensure the directory exists
    if not os.path.exists(directory):
        print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Directory '{directory}' does not exist.")
        return

    # List all files and directories in the directory
    for item in os.listdir(directory):
        item_path = os.path.join(directory, item)

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
    # Process the BOM file
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
                    update_bom_instance(connector_name, current_mpn, columns[supplier_index], columns[desc_simple_index], columns[id_index], 0, 0)

    """
        if current_desc_simple == "Connector":
            current_mpn = columns[mpn_index]
    
            

            

                

        #if "Description Simple" == "Connector" 
            #for each connector in yaml
                #if "mpn" in yaml == "MPN" in harness bom
                    #if connector has any backshell as an additional part
                        #backshelldrivenrotation = lookup backshell driven location
                        #backshelldrivenoffset = lookup backshell driven offset
                    #update_bom_instance(connector + backshell driven stuff)

                
"""

def update_bom_instance(instance_name, mpn, supplier, bomid, instance_type, rotation, offset):
    #make sure the main directory is there
    os.makedirs(dirpath("drawing-instances"), exist_ok=True)

    #make sure the directory in question is there
    if(instance_type == "Backshell"):
        x = f"{instance_name}-bs"
    else:
        x = instance_name
    os.makedirs(os.path.join(dirpath("drawing-instances"),x), exist_ok=True)
    
    instance_dirpath = os.path.join(dirpath("drawing-instances"),x)

    #import from library
    import_file_from_harnice_library(supplier,mpn,f"{mpn}-drawing.svg")
    import_file_from_harnice_library(supplier,mpn,f"{mpn}-attributes.json")
    
    #remember which files are supposed to exist so we can later delete the old ones
    add_filename_to_drawing_instance_list(instance_name)

    #reference the drawing filepath, not included in filepath() because each project file structure is different
    instance_svg_path = os.path.join(instance_dirpath, f"{partnumber("pn-rev")}-{instance_name}.svg")

    #create a new instance file if it doesn't exist yet
    if not os.path.exists(instance_svg_path):
        print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Generating  instance svg {partnumber("pn-rev")}-{instance_name}.svg")
        os.makedirs(instance_dirpath, exist_ok=True)

        # Write SVG declaration
        svg_content = '<svg xmlns="http://www.w3.org/2000/svg"></svg>'

        with open(instance_svg_path, 'w') as blank_svg:
            blank_svg.write(svg_content)

        # Verify the file content
        with open(instance_svg_path, 'r') as verify_svg:
            content = verify_svg.read()

        print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Created new connector instance SVG {instance_name} with MPN: {mpn}")

        add_entire_svg_file_contents_to_group(instance_svg_path,"connector-drawing")
        find_and_replace_svg_group(instance_svg_path, os.path.join(library_used_path, "connector_definitions", current_mpn, f"{current_mpn}-drawing.svg"), "connector-drawing")
        add_entire_svg_file_contents_to_group(instance_svg_path, "connector-instance-rotatables")
        add_entire_svg_file_contents_to_group(instance_svg_path, f"unique-connector-instance-{instance_name}")
        apply_bubble_transforms_to_flagnote_group(instance_svg_path)
                        
    else: 
        print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Preserving existing contents of {instance_name} instance file. ")
      
    # Rotate SVG group "connector-drawing" to match the average segment angle
    connector_angle = -1* retrieve_angle_of_connector(instance_name)
    rotate_svg_group(instance_svg_path, "connector-instance-rotatables", connector_angle)
    update_flagnotes_of_instance(instance_svg_path, instance_name, connector_angle, bomid)


def update_connector_instances():
    # Get current working directory and paths
    library_used_path = dirpath("library_used")
    drawing_instances_by_connector_name_path = dirpath("drawing-instances")

    # Load YAML file
    with open(filepath("wireviz yaml"), 'r') as yaml_file:
        yaml_data = yaml.safe_load(yaml_file)

    # Process the BOM file
    with open(filepath("electrical bom"), 'r') as bom_file:
        # Read the header to identify the index of "MPN"
        header = bom_file.readline().strip().split("\t")
        if "MPN" not in header:
            print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: 'MPN' column not found in the BOM file.")
            return
        mpn_index = header.index("MPN")
        if "Id" not in header:
            print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: 'MPN' column not found in the BOM file.")
            return
        id_index = header.index("Id")

        # Iterate through the rows
        for line in bom_file:
            columns = line.strip().split("\t")
            if len(columns) <= mpn_index:
                continue  # Skip rows with insufficient columns
            current_mpn = columns[mpn_index]
            print(f"#    #    ############ WORKING ON BOM ITEM {current_mpn} ############")

            # Match current MPN with the connectors in YAML
            for connector_name, connector_data in yaml_data.get("connectors", {}).items():
                try:
                    if connector_data.get("mpn") == current_mpn:
                        print(f"#    #    #    ############ WORKING ON CONNECTOR {connector_name} ############")
                        connector_svg_dir = os.path.join(drawing_instances_by_connector_name_path, connector_name)
                        os.makedirs(connector_svg_dir, exist_ok=True)
                        connector_svg_path = os.path.join(connector_svg_dir, f"{partnumber("pn-rev")}-{connector_name}.svg")
                        

                        # Ensure directory for MPN exists and import files if necessary
                        import_file_from_harnice_library(
                            connector_data.get("supplier"),
                            f"connector_definitions/{current_mpn}",
                            f"{current_mpn}-drawing.svg"
                        )

                        # Generate blank SVG only if it doesn't exist
                        add_filename_to_drawing_instance_list(basename(dirname(connector_svg_path)))
                        
                        if not os.path.exists(connector_svg_path):
                            print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Generating connector instance svg {partnumber("pn-rev")}-{connector_name}.svg")
                            os.makedirs(drawing_instances_by_connector_name_path, exist_ok=True)

                            # Write SVG declaration
                            svg_content = '<svg xmlns="http://www.w3.org/2000/svg"></svg>'

                            with open(connector_svg_path, 'w') as blank_svg:
                                blank_svg.write(svg_content)

                            # Verify the file content
                            with open(connector_svg_path, 'r') as verify_svg:
                                content = verify_svg.read()

                            print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Created new connector instance SVG {connector_name} with MPN: {current_mpn}")

                            add_entire_svg_file_contents_to_group(connector_svg_path,"connector-drawing")
                            find_and_replace_svg_group(connector_svg_path, os.path.join(library_used_path, "connector_definitions", current_mpn, f"{current_mpn}-drawing.svg"), "connector-drawing")
                            add_entire_svg_file_contents_to_group(connector_svg_path, "connector-instance-rotatables")
                            add_entire_svg_file_contents_to_group(connector_svg_path, f"unique-connector-instance-{connector_name}")
                            apply_bubble_transforms_to_flagnote_group(connector_svg_path)

                        
                        else: 
                            print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Preserving existing contents of {connector_name} instance file. ")

                    
                        
                        # Rotate SVG group "connector-drawing" to match the average segment angle
                        connector_angle = -1* retrieve_angle_of_connector(connector_name)
                        rotate_svg_group(connector_svg_path, "connector-instance-rotatables", connector_angle)
                        update_flagnotes_of_instance(connector_svg_dir, connector_name, connector_angle, columns[id_index])

                except Exception as e:
                    print(f"Error processing {connector_name}: {e}")


def update_segment_instances():
    # Get current working directory and paths
    current_dir = os.getcwd()
    formboard_graph_definition_path = os.path.join(current_dir, f"{partnumber("pn-rev")}-formboard-graph-definition.json")
    
    # Load JSON data
    try:
        with open(formboard_graph_definition_path, 'r') as json_file:
            graph_data = json.load(json_file)
    except FileNotFoundError:
        print(f"Error: File {formboard_graph_definition_path} not found.")
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
            os.makedirs(os.path.join(current_dir, "drawing-instances", segment_name), exist_ok=True)

            output_filename = os.path.join(current_dir, "drawing-instances", segment_name, f"{partnumber("pn-rev")}-{segment_name}.svg")
            
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
    current_dir = os.getcwd()
    node_locations_path = os.path.join(current_dir, "support-do-not-edit", "formboard_data", f"{partnumber("pn-rev")}-formboard-node-locations-px.json")
    output_svg_path = os.path.join(current_dir, "support-do-not-edit", "master-svgs", f"{partnumber("pn-rev")}-formboard-master.svg")
    segment_locations_path = os.path.join(current_dir, "support-do-not-edit", "formboard_data", f"{partnumber("pn-rev")}-formboard-segment-to-from-center.json")

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

def replace_all_connector_groups():
    """Replace all connector groups in the target SVG with their corresponding source SVG groups."""
    current_dir = os.getcwd()
    formboard_graph_definition_path = os.path.join(current_dir, f"{partnumber("pn-rev")}-formboard-graph-definition.json")

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
    """
    Retrieve the angle of the specified connector from the JSON file.

    Args:
        connectorname (str): The name of the connector (e.g., "X1").

    Returns:
        float: The angle of the specified connector.

    Raises:
        FileNotFoundError: If the JSON file does not exist.
        KeyError: If the connector name does not exist in the JSON data.
    """
    # Construct the path to the JSON file
    current_dir = os.getcwd()
    file_path = os.path.join(current_dir, "support-do-not-edit", "formboard_data", 
                             f"{partnumber("pn-rev")}-formboard-node-locations-inches.json")
    
    # Check if the file exists
    #this used to work but something got fucked up and now i cant tell what it used to do
    #if not os.path.isfile(file_path):
        #partnumber("pn-rev") FileNotFoundError(f"File not found: {file_path}")
    
    # Load the JSON data
    with open(file_path, "r") as file:
        data = json.load(file)
    
    # Retrieve the angle for the specified connector
    try:
        angle = data[connectorname]["angle"]
    except KeyError:
        raise KeyError(f"Connector '{connectorname}' not found in the JSON data.")
    
    return angle

def retrieve_angle_of_segment(segmentname):
    # Construct the path to the JSON file
    current_dir = os.getcwd()
    file_path = os.path.join(current_dir, f"{partnumber("pn-rev")}-formboard-graph-definition.json")
    
    # Check if the file exists
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    # Load the JSON data
    with open(file_path, "r") as file:
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
    delete_unmatched_files(os.path.join(os.getcwd(),"drawing-instances"))
    print("#    ############ ADDING EVERYTHING TO FORMBOARD MASTER SVG ############")
    update_formboard_master_svg()
    print("#    ############ REPLACING ALL CONNECTOR GROUPS IN FORMBOARD MASTER ############")
    replace_all_connector_groups()
    print("#    ############ REPLACING ALL INSTANCE GROUPS IN FORMBOARD MASTER ############")
    replace_all_segment_groups()

if __name__ == "__main__":
    regen_formboard()