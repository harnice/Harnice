import os
import os.path
import json
import time
import subprocess
import shutil
from os.path import basename
from inspect import currentframe
import xml.etree.ElementTree as ET
import re
from dotenv import load_dotenv, dotenv_values
import file

#used to be svg_add_groups
def add_entire_svg_file_contents_to_group(filepath, new_group_name):
    """
    Modify the SVG file by wrapping its inner contents (excluding the <svg> tag and attributes)
    in a group and adding a new empty group.
    
    Args:
        filepath (str): Path to the SVG file.
        new_group_name (str): The name of the new group to wrap the contents and add a placeholder.
    """
    if os.path.exists(filepath):
        try:
            # Read the original SVG content
            with open(filepath, "r", encoding="utf-8") as file:
                svg_content = file.read()
            
            # Extract contents inside the <svg>...</svg>, excluding the <svg> tag and its attributes
            match = re.search(r'<svg[^>]*>(.*?)</svg>', svg_content, re.DOTALL)
            if not match:
                raise ValueError("File does not appear to be a valid SVG or has no inner contents.")
            
            inner_content = match.group(1).strip()

            # Create the updated SVG content
            updated_svg_content = (
                f'<svg xmlns="http://www.w3.org/2000/svg">\n'
                f'  <g id="{new_group_name}-contents-start">\n'
                f'    {inner_content}\n'
                f'  </g>\n'
                f'  <g id="{new_group_name}-contents-end"></g>\n'
                f'</svg>\n'
            )

            # Write the updated content back to the file
            with open(filepath, "w", encoding="utf-8") as file:
                file.write(updated_svg_content)

            print(
                f"from {basename(__file__)} > {currentframe().f_code.co_name}: "
                f"Added entire contents of {os.path.basename(filepath)} to a new group {new_group_name}-contents-start"
            )
        except Exception as e:
            print(
                f"from {basename(__file__)} > {currentframe().f_code.co_name}: "
                f"Error adding contents of {os.path.basename(filepath)} to a new group {new_group_name}: {e}"
            )
    else:
        print(
            f"from {basename(__file__)} > {currentframe().f_code.co_name}: "
            f"Trying to add contents of {os.path.basename(filepath)} to a new group but file does not exist."
        )

def rename_file(old_name, new_name, print_report):
    """Rename a file from old_name to new_name."""
    if os.path.exists(old_name):
        try:
            os.rename(old_name, new_name)
            if print_report:
                print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Renamed {old_name} to {new_name}")
        except OSError as e:
            print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Error renaming file {old_name} to {new_name}: {e}")
    else:
        if print_report:
            print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: File {old_name} does not exist, cannot rename.")




def file_exists_in_directory(search_for_filename, directory="."):
    """
    Checks if a file exists in the specified directory.
    """
    return os.path.isfile(os.path.join(directory, search_for_filename))


def import_file_from_harnice_library(domain, library_subpath, lib_file):
    """
    Copies a file from a Harnice library to a local 'library_used' directory with the same subpath structure.
    """
    load_dotenv()
    print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Importing library {lib_file}:")
    # Step 1: Check if lib_file exists in Harnice library
    harnice_path = os.getenv(domain)
    source_file_path = os.path.join(harnice_path, library_subpath)
    
    if not os.path.isfile(os.path.join(source_file_path,lib_file)):
        print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Failed to import library: file '{lib_file}' not found in {source_file_path}")
        return False

    # Step 2: Check if the file already exists in the local library
    target_directory = os.path.join(os.getcwd(), "library_used", library_subpath)
    target_filename = os.path.join(target_directory, lib_file)
    
    if os.path.isfile(target_filename):
        print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Library instance '{lib_file}' already exists in this part number's library_used. If you wish to replace it, remove the instance and rerun this command.")
        return True

    # Step 3: Ensure the target directory structure exists
    if not os.path.exists(target_directory):
        os.makedirs(target_directory)
        print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Added directory '{library_subpath}' to '{file.partnumber("pn-rev")}/library_used/'.")

    # Step 4: Copy the file from Harnice library to the target directory
    shutil.copy(os.path.join(source_file_path,lib_file), target_filename)
    print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: File '{lib_file}' added to '{file.partnumber("pn-rev")}/library_used/{library_subpath}'.")

    return True
    #returns True if import was successful or if already exists 
    #returns False if library not found (try and import this again?)


def find_and_replace_svg_group(target_svg_filepath, source_svg_filepath, group_id):
    import os

    def get_filename(filepath):
        return os.path.basename(filepath)

    try:
        # Read the source SVG content
        with open(source_svg_filepath, 'r') as source_file:
            source_svg_content = source_file.read()

        # Read the target SVG content
        with open(target_svg_filepath, 'r') as target_file:
            target_svg_content = target_file.read()

        # Define the start and end tags (the key string that signifies the start and end of the group)
        start_tag = f'id="{group_id}-contents-start"'
        end_tag = f'id="{group_id}-contents-end"'
        success = 0 #value that is returned: 1 for success, 0 for failure

        # Find the start and end indices of the group in the source SVG.
        source_start_index = source_svg_content.find(start_tag)
        if source_start_index == -1:
            print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Source start tag <{start_tag}> not found in file <{get_filename(source_svg_filepath)}>.")
            success = 0
            return success
        source_end_index = source_svg_content.find(end_tag)
        if source_end_index == -1:
            print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Source end tag <{end_tag}> not found in file <{get_filename(source_svg_filepath)}>.")
            success = 0
            return success

        # Find the start and end indices of the group in the target SVG.
        target_start_index = target_svg_content.find(start_tag)
        if target_start_index == -1:
            print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Target start tag <{start_tag}> not found in file <{get_filename(target_svg_filepath)}>.")
            success = 0
            return success
        target_end_index = target_svg_content.find(end_tag)
        if target_end_index == -1:
            print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Target end tag <{end_tag}> not found in file <{get_filename(target_svg_filepath)}>.")
            success = 0
            return success

        # Grab the group and save it to replace
        replacement_group_content = source_svg_content[source_start_index:source_end_index]

        # Replace the target group content with the source group content
        updated_svg_content = (
            target_svg_content[:target_start_index]
            + replacement_group_content
            + target_svg_content[target_end_index:]
        )

        # Overwrite the target file with the updated content
        try:
            with open(target_svg_filepath, 'w') as updated_file:
                updated_file.write(updated_svg_content)
        except Exception as e:
            print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Error writing to file <{get_filename(target_svg_filepath)}>: {e}")
            success = 0

        print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Copied group <{group_id}> from <{get_filename(source_svg_filepath)}> and pasted it into <{get_filename(target_svg_filepath)}>.")
        success = 1
    
    except Exception as e:
        print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Error processing files <{get_filename(source_svg_filepath)}> and <{get_filename(target_svg_filepath)}>: {e}")
        success = 0

    return success


def rotate_svg_group(svg_path, group_name, angle):
    """
    Modify the rotation of a specific group in an SVG file by directly searching and replacing text.
    
    Args:
        svg_path (str): Path to the SVG file.
        angle (float): The new rotation angle to apply.
    """
    id_string = "id=" + '"' + group_name + "-contents-start" + '"'
    try:
        # Read the file content
        with open(svg_path, 'r', encoding='utf-8') as svg_file:
            lines = svg_file.readlines()

        # Search for the group by ID and modify the rotation
        group_found = False
        for i, line in enumerate(lines):
            if id_string in line:
                if 'transform="rotate(' in line:
                    # Group already has a rotation, update it
                    lines[i] = re.sub(r'rotate\(([^)]+)\)', f'rotate({angle})', line)
                    group_found = True
                    break
                else:
                    # Group exists but does not have a rotation, add it
                    lines[i] = line.strip().replace('>', f' transform="rotate({angle})">') + '\n'
                    group_found = True
                    break

        # If the group is not found, raise an error
        if not group_found:
            raise ValueError(f"{group_name} group not initialized correctly.")

        # Write the modified content back to the file
        with open(svg_path, 'w', encoding='utf-8') as svg_file:
            svg_file.writelines(lines)

        print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Rotated {group_name} to {angle} deg in {os.path.basename(svg_path)}.")

    except FileNotFoundError:
        print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Error: File not found - {svg_path}")
    except ValueError as e:
        print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Error: {e}")
    except Exception as e:
        print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: An unexpected error occurred: {e}")

#standard punctuation:
    #  .  separates between name hierarchy levels
    #  _  means nothing, basically a space character
    #  -  if multiple instances are found at the same hierarchy level with the same name, this separates name from unique instance identifier

#here's the ultimate definition of all Harnice project files:

#syntax:
#"filename": "filekey"

#filename is the actual file name with a suffix
#filekey is the shorthand reference for it with no suffix
def harnice_file_structure():
    return {
            "drawing_instances":{},
            "library_used":{},
            "support_do_not_edit": {
                "boms":{
                    f"{file.partnumber("pn-rev")}.esch_electrical_bom.tsv":"electrical bom",
                    f"{file.partnumber("pn-rev")}.harness_bom.tsv":"harness bom",
                    f"{file.partnumber("pn-rev")}.mechanical_bom.tsv":"mechanical bom",
                    f"{file.partnumber("pn-rev")}.instances_list.tsv":"instances list"
                },
                "formboard_data": {
                    f"{file.partnumber("pn-rev")}.connections_to_graph.json":"connections to graph",
                    f"{file.partnumber("pn-rev")}.formboard_node_locations_inches.json":"formboard node locations inches",
                    f"{file.partnumber("pn-rev")}.formboard_node_locations_px.json":"formboard node locations px",
                    f"{file.partnumber("pn-rev")}.formboard_segment_to_from_center.json":"formboard segment to from center",
                    f"{file.partnumber("pn-rev")}.formboard_graph_definition.svg":"formboard graph definition svg"
                },
                "master_svgs": {
                    f"{file.partnumber("pn-rev")}.bom_table_master.svg":"bom table master svg",
                    f"{file.partnumber("pn-rev")}.esch_master.svg":"esch master svg",
                    f"{file.partnumber("pn-rev")}.formboard_master.svg":"formboard master svg",
                    f"{file.partnumber("pn-rev")}.tblock_master.svg":"tblock master svg",
                    f"{file.partnumber("pn-rev")}.revhistory_master.svg":"revhistory master svg",
                    f"{file.partnumber("pn-rev")}.buildnotes_master.svg":"buildnotes master svg"
                },
                "wirelists": {
                    f"{file.partnumber("pn-rev")}.wirelist_nolengths.tsv":"wirelist nolengths",
                    f"{file.partnumber("pn-rev")}.wirelist_lengths.tsv":"wirelist lengths"
                },
                f"{file.partnumber("pn-rev")}.tblock_master_text.json":"tblock master text",
                f"{file.partnumber("pn-rev")}.flagnote_instance_matrix.tsv":"flagnote instance matrix"
            },
            "wireviz_outputs":{
                f"{file.partnumber("pn-rev")}.bom.tsv":"wireviz bom",
                f"{file.partnumber("pn-rev")}.html":"wireviz html",
                f"{file.partnumber("pn-rev")}.png":"wireviz png",
                f"{file.partnumber("pn-rev")}.svg":"wireviz svg"
            },
            f"{file.partnumber("pn-rev")}.formboard_graph_definition.json":"formboard graph definition",
            f"{file.partnumber("pn-rev")}.harnice_output.svg":"harnice output",
            f"{file.partnumber("pn-rev")}.buildnotes.tsv":"buildnotes tsv",
            f"{file.partnumber("pn-rev")}.yaml":"harness yaml"
        }

def generate_file_structure():
    os.makedirs(dirpath("drawing_instances"), exist_ok=True)
    os.makedirs(dirpath("library_used"), exist_ok=True)
    os.makedirs(dirpath("support_do_not_edit"), exist_ok=True)
    os.makedirs(dirpath("boms"), exist_ok=True)
    os.makedirs(dirpath("formboard_data"), exist_ok=True)
    os.makedirs(dirpath("master_svgs"), exist_ok=True)
    os.makedirs(dirpath("wirelists"), exist_ok=True)
    os.makedirs(dirpath("wireviz_outputs"), exist_ok=True)

def filepath(target_value):
    #returns the filepath/filename of a filekey. 
    """
    Recursively searches for a value in a nested JSON structure and returns the path to the element containing that value.

    Args:
        target_value (str): The value to search for.

    Returns:
        list: A list of container names leading to the element containing the target value, or None if not found.
    """

    def recursive_search(data, path):
        if isinstance(data, dict):
            for key, value in data.items():
                if value == target_value:
                    return path + [key]
                result = recursive_search(value, path + [key])
                if result:
                    return result
        elif isinstance(data, list):
            for index, item in enumerate(data):
                if item == target_value:
                    return path + [f"[{index}]"]
                result = recursive_search(item, path + [f"[{index}]"])
                if result:
                    return result
        return None

    path_value = recursive_search(harnice_file_structure(), [])
    if not path_value:
        raise TypeError(f"Could not find filepath of {target_value}.")
    return os.path.join(os.getcwd(),*path_value)

def dirpath(target_key):
    #returns the path of a directory you know the name of. use that directory name as the argument. 

    def recursive_search(data, path):
        if isinstance(data, dict):
            for key, value in data.items():
                if key == target_key:
                    return path + [key]
                result = recursive_search(value, path + [key])
                if result:
                    return result
        elif isinstance(data, list):
            for index, item in enumerate(data):
                result = recursive_search(item, path + [f"[{index}]"])
                if result:
                    return result
        return None

    path_key = recursive_search(harnice_file_structure(), [])
    if not path_key:
        raise TypeError(f"Could not find directory {target_key}.")
    return os.path.join(os.getcwd(),*path_key)

def filename(target_value):
    #returns the filename of a filekey. 
    """
    Recursively searches for a value in a nested JSON structure and returns the key containing that value.

    Args:
        target_value (str): The value to search for.

    Returns:
        str: The key containing the target value, or None if not found.
    """

    def recursive_search(data):
        if isinstance(data, dict):
            for key, value in data.items():
                if value == target_value:
                    return key
                result = recursive_search(value)
                if result:
                    return result
        elif isinstance(data, list):
            for item in data:
                result = recursive_search(item)
                if result:
                    return result
        return None

    if not recursive_search(harnice_file_structure()):
        raise TypeError(f"Could not find filename of key {target_value}.")

    return recursive_search(harnice_file_structure())

#example:
if __name__ == "__main__":

    #returns the filepath of a filekey. 
    #print(filepath("esch master svg"))

    #returns the path of a directory you know the name of. use that directory name as the argument. 
    #print(dirpath("formboard data"))

    #returns the filename of a filekey
    print(dirpath("drawing_instances"))