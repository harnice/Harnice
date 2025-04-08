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
import fileio

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

def find_and_replace_svg_group(target_svg_filepath, source_svg_filepath, group_id):
    import os

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
            print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Source start tag <{start_tag}> not found in file <{get_fileio.name(source_svg_filepath)}>.")
            success = 0
            return success
        source_end_index = source_svg_content.find(end_tag)
        if source_end_index == -1:
            print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Source end tag <{end_tag}> not found in file <{get_fileio.name(source_svg_filepath)}>.")
            success = 0
            return success

        # Find the start and end indices of the group in the target SVG.
        target_start_index = target_svg_content.find(start_tag)
        if target_start_index == -1:
            print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Target start tag <{start_tag}> not found in file <{get_fileio.name(target_svg_filepath)}>.")
            success = 0
            return success
        target_end_index = target_svg_content.find(end_tag)
        if target_end_index == -1:
            print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Target end tag <{end_tag}> not found in file <{get_fileio.name(target_svg_filepath)}>.")
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
            print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Error writing to file <{get_fileio.name(target_svg_filepath)}>: {e}")
            success = 0

        print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Copied group <{group_id}> from <{get_fileio.name(source_svg_filepath)}> and pasted it into <{get_fileio.name(target_svg_filepath)}>.")
        success = 1
    
    except Exception as e:
        print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Error processing files <{get_fileio.name(source_svg_filepath)}> and <{get_fileio.name(target_svg_filepath)}>: {e}")
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