import os
from os.path import basename
import json
import xml.etree.ElementTree as ET
import yaml  # PyYAML for parsing YAML files
from utility import import_file_from_harnice_library, find_and_replace_svg_group, pn_from_dir, add_entire_svg_file_contents_to_group, find_and_replace_svg_group

def pn_from_dir():
    """Extract the project name from the current directory name."""
    return os.path.basename(os.getcwd())

def update_connector_instances():
    # Get current working directory and paths
    current_dir = os.getcwd()
    library_used_path = os.path.join(current_dir, "library_used")
    yaml_path = os.path.join(current_dir, f"{pn_from_dir()}.yaml")
    esch_electrical_bom_path = os.path.join(current_dir, "support-do-not-edit", "boms", f"{pn_from_dir()}-esch-electrical-bom.tsv")
    drawing_instances_by_connector_name_path = os.path.join(current_dir, "drawing-instances-by-connector-name")

    # Load YAML file
    with open(yaml_path, 'r') as yaml_file:
        yaml_data = yaml.safe_load(yaml_file)

    # Process the BOM file
    try:
        with open(esch_electrical_bom_path, 'r') as bom_file:
            # Read the header to identify the index of "MPN"
            header = bom_file.readline().strip().split("\t")
            if "MPN" not in header:
                print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: 'MPN' column not found in the BOM file.")
                return
            mpn_index = header.index("MPN")

            # Iterate through the rows
            for line in bom_file:
                columns = line.strip().split("\t")
                if len(columns) <= mpn_index:
                    continue  # Skip rows with insufficient columns
                current_mpn = columns[mpn_index]

                # Match current MPN with the connectors in YAML
                for connector_name, connector_data in yaml_data.get("connectors", {}).items():
                    if connector_data.get("mpn") == current_mpn:
                        mpn_path = os.path.join(library_used_path, current_mpn)
                        connector_svg_path = os.path.join(drawing_instances_by_connector_name_path, f"{pn_from_dir()}-{connector_name}.svg")

                        # Ensure directory for MPN exists and import files if necessary
                        import_file_from_harnice_library(
                            connector_data.get("supplier"),
                            f"connector_definitions/{current_mpn}",
                            f"{current_mpn}-drawing.svg"
                        )

                        # Generate blank SVG if it doesn't exist
                        if not os.path.exists(connector_svg_path):
                            print(f"Generating connector instance svg {pn_from_dir()}-{connector_name}.svg")
                            os.makedirs(drawing_instances_by_connector_name_path, exist_ok=True)
                            with open(connector_svg_path, 'w') as blank_svg:
                                blank_svg.write('<svg xmlns="http://www.w3.org/2000/svg"></svg>')
                            add_entire_svg_file_contents_to_group(
                                connector_svg_path,
                                "connector-drawing"
                            )

                        # Replace SVG group
                        find_and_replace_svg_group(
                            connector_svg_path,
                            os.path.join(library_used_path,"connector_definitions",current_mpn,f"{current_mpn}-drawing.svg"),
                            "connector-drawing"
                        )

                        add_entire_svg_file_contents_to_group(connector_svg_path,f"unique-connector-instance-{connector_name}")

                        print(f"Processed connector: {connector_name} with MPN: {current_mpn}")

    except Exception as e:
        print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Error processing BOM file: {e}")

def update_formboard_master_svg():
    current_dir = os.getcwd()
    yaml_path = os.path.join(current_dir, f"{pn_from_dir()}.yaml")
    node_locations_path = os.path.join(current_dir, "support-do-not-edit", "formboard_data", f"{pn_from_dir()}-formboard-node-locations-px.json")
    output_svg_path = os.path.join(current_dir, "support-do-not-edit", "master-svgs", f"{pn_from_dir()}-formboard-master.svg")

    # Read the YAML file
    with open(yaml_path, 'r') as yaml_file:
        yaml_data = yaml.safe_load(yaml_file)
    
    # Read the node locations JSON file
    with open(node_locations_path, 'r') as json_file:
        node_locations = json.load(json_file)
    
    # Extract connectors
    connectors = yaml_data.get("connectors", {})
    
    # Create the root SVG element
    svg = ET.Element("svg", xmlns="http://www.w3.org/2000/svg", version="1.1")
    
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
    
    print(f"SVG file {'overwritten' if os.path.exists(output_svg_path) else 'created'} at: {output_svg_path}")

def replace_all_connector_groups():
    """Replace all connector groups in the target SVG with their corresponding source SVG groups."""
    current_dir = os.getcwd()
    yaml_path = os.path.join(current_dir, f"{pn_from_dir()}.yaml")
    
    # Read the YAML file
    with open(yaml_path, 'r') as yaml_file:
        yaml_data = yaml.safe_load(yaml_file)
    
    # Extract connectors from the YAML
    connectors = yaml_data.get("connectors", {})
    
    for connector_name in connectors:
        # Define the target and source SVG paths
        target_svg_filepath = os.path.join(current_dir, "support-do-not-edit", "master-svgs", f"{pn_from_dir()}-formboard-master.svg")
        source_svg_filepath = os.path.join(current_dir, "drawing-instances-by-connector-name", f"{pn_from_dir()}-{connector_name}.svg")
        
        # Call the function to replace the group
        find_and_replace_svg_group(target_svg_filepath, source_svg_filepath, f"unique-connector-instance-{connector_name}")

def regen_formboard():
    update_connector_instances()
    update_formboard_master_svg()
    replace_all_connector_groups()


if __name__ == "__main__":
    regen_formboard()