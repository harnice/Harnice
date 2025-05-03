import os
import re
import xml.etree.ElementTree as ET
import csv
import fileio
from os.path import basename
from inspect import currentframe

buildnotes_filepath = fileio.path("buildnotes tsv")
revnotes_filepath = fileio.path("revision history")


def update_flagnotes_of_instance(target_filepath, instance_name, rotation_angle, bomid):
    instance_drawing_filename = f"{fileio.partnumber("pn-rev")}-{instance_name}.svg"
    instance_drawing_filepath = os.path.join(target_filepath, instance_drawing_filename)
    instance_flagnotes_filename = f"{instance_name}-instance-flagnotes.svg"
    instance_flagnotes_filepath = os.path.join(target_filepath, instance_flagnotes_filename)
    generate_instance_flagnotes(instance_name,instance_flagnotes_filename,instance_flagnotes_filepath,rotation_angle,bomid)
    for i in range(0, 11):
        note_exists_for_instance = svg_utils.find_and_replace_svg_group(instance_drawing_filepath, instance_flagnotes_filepath, f"as-printed-flagnote-{i}")
        
        if note_exists_for_instance == 1:
            #make leader visible
            update_note_opacity(instance_drawing_filepath, f"path-{i}", 1)
        else: 
            #make leader transparent
            update_note_opacity(instance_drawing_filepath, f"path-{i}", 0)


def look_for_buildnotes_file():
    # Check if the file exists
    if os.path.exists(buildnotes_filepath):
        return
    
    else:
        # Define the columns for the TSV file
        columns = ["notenumber", "notedescription", "affectedinstances"]

        # Write the TSV file
        with open(buildnotes_filepath, 'w') as file:
            file.write('\t'.join(columns) + '\n')
    
        print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: File '{fileio.name("buildnotes tsv")}' not found. Generating a blank file.")


def find_buildnotes_of_instance(instance, note_list_filepath):
    #change this so function name is find_flagnotes and arguments are "filepath" and "instance"
    #this way you can search buildnotes, rev flagnotes, and other in the same function
    instance_buildnotes = []

    try:
        with open(note_list_filepath, 'r') as file:
            header = file.readline().strip().split('\t')
            affectedinstances_index = header.index("affectedinstances")
            notenumber_index = header.index("notenumber")

            for line in file:
                row = line.strip().split('\t')

                # Ensure row has same length as header, filling missing values with None
                row = [value if value else None for value in row] + [None] * (len(header) - len(row))

                affected_instances = row[affectedinstances_index]
                if affected_instances:
                    for affected_instance in affected_instances.split(","):
                        clean_instance = affected_instance.strip().replace('"', '').replace("'", "")
                        if instance == clean_instance:
                            reference_number = row[notenumber_index]
                            if reference_number:
                                instance_buildnotes.append(reference_number)
                            break

    except FileNotFoundError:
        print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Error: The file {buildnotes_filepath} was not found.")
    except Exception as e:
        print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: An error occurred: {e}")

    return instance_buildnotes
    

def generate_instance_flagnotes(instance, instance_flagnotes_filename, instance_flagnotes_filepath,rotation_angle,bomid):
    # Create a new SVG file and write a basic SVG structure
    with open(instance_flagnotes_filepath, 'w') as f:
        f.write('<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="500" height="500">')

    #find all relevant pieces of info and add them to note svg as note-indices
    bubble_location_index = 0

    #to-do: add refdes as note index
    generate_note_svg(instance_flagnotes_filepath, "rectangle-long", instance, bubble_location_index, rotation_angle)
    bubble_location_index += 1

    #add bom item as note index
    generate_note_svg(instance_flagnotes_filepath, "circle", bomid, bubble_location_index, rotation_angle)
    bubble_location_index += 1

    #to-do: add revs as note index
    revnotes = find_buildnotes_of_instance(instance, revnotes_filepath)
    for revnote in revnotes:
        generate_note_svg(instance_flagnotes_filepath, "triangle-down", revnote, bubble_location_index, rotation_angle)
        bubble_location_index += 1

    # Iterate through each build note and update the SVG
    buildnotes = find_buildnotes_of_instance(instance, buildnotes_filepath)
    for buildnote in buildnotes:
        generate_note_svg(instance_flagnotes_filepath, "triangle-up", buildnote, bubble_location_index, rotation_angle)
        bubble_location_index += 1

    """
    if bubble_location_index <= 10:
        for i in range(bubble_location_index, 11):
            generate_note_svg(instance_flagnotes_filepath, "blank", "", bubble_location_index, 0)
            i += 1
            bubble_location_index += 1
    """

    with open(instance_flagnotes_filepath, 'a') as f:
        f.write('</svg>')



def generate_note_svg(target_file, shape, text_in_bubble, bubble_location_index, note_angle):
    """
    Generates SVG code for a specified shape and appends it to the target_file.
    Ensures proper indentation and newlines between elements for readability.
    The target_file is expected to be a valid file path string.
    """
    # Open the file in append mode
    with open(target_file, "a") as file:
        # Start the groups
        group_start = f'\n<g id="as-printed-flagnote-{bubble_location_index}-contents-start">\n'
        file.write(group_start)

        group_start = f'\n<g id="flagnote-{shape}-{text_in_bubble}-rotatables-contents-start">\n'
        file.write(group_start)

        # Add shape-specific elements
        if shape == "circle":
            circle_element = f"""
    <circle
    cx="0"
    cy="0"
    r="7"
    fill="#ffffff"
    stroke="#000000"
    stroke-width="0.177271"
    id="flagnote-{shape}-{text_in_bubble}-bubble"/>\n"""
            file.write(circle_element)

        elif shape == "triangle-up":
            triangle_up_element = f"""  
    <polygon
    points="-9.60,6.40 9.60,6.40 0.00,-12.80"
    fill="#ffffff"
    stroke="#000000"
    stroke-width="0.67"
    id="flagnote-{shape}-{text_in_bubble}-bubble"/>\n"""
            file.write(triangle_up_element)

        elif shape == "triangle-down":
            triangle_down_element = f"""
    <polygon
    points="0.00,12.80 -9.60,-6.40 9.60,-6.40"
    fill="#ffffff"
    stroke="#000000"
    stroke-width="0.67"
    id="flagnote-{shape}-{text_in_bubble}-bubble"/>\n"""
            file.write(triangle_down_element)

        elif shape == "rectangle-long":
            square_element = f"""
    <polygon
    points="-50,7.5 50,7.5 50,-7.5 -50,-7.5"
    fill="#ffffff"
    stroke="#000000"
    stroke-width="0.67"
    id="flagnote-{shape}-{text_in_bubble}-bubble"/>\n"""
            file.write(square_element)

        # Add the text element
        text_element = f"""
    <text
    x="0"
    y="3.5"
    style="font-size:9px;font-family:Arial;text-align:center;text-anchor:middle;fill:#000000;stroke-width:0.576;stroke-dasharray:none"
    id="flagnote-{shape}-{text_in_bubble}-text">{text_in_bubble}</text>\n"""
        file.write(text_element)

        # End the groups
        group_end = f'</g>\n<g id="flagnote-{shape}-{text_in_bubble}-rotatables-contents-end">\n</g>\n'
        file.write(group_end)
        group_end = f'</g>\n<g id="as-printed-flagnote-{bubble_location_index}-contents-end">\n</g>\n'
        file.write(group_end)

    svg_utils.rotate_svg_group(target_file, f"flagnote-{shape}-{text_in_bubble}-rotatables", -1 * note_angle)


def apply_bubble_transforms_to_flagnote_group(file_path):
    for i in range(0, 11):
        note_location = extract_note_location(file_path, i)
        translate_note_group(file_path, i, note_location)

def translate_note_group(file_path, bubble_location_index, note_coords):
    # Construct the search string and replacement string
    search_string = fr'<g id="as-printed-flagnote-{bubble_location_index}-translatables">'
    replacement_string = (
        f'<g id="as-printed-flagnote-{bubble_location_index}-translatables" '
        f'transform="translate({note_coords[0]}, {note_coords[1]})">'
    )


    try:
        # Read the file content
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()

        # Check if the search string exists in the file
        if not search_string in content:
            print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Search string {search_string} not found in file {os.path.basename(file_path)}.")

        else:
            # Replace the string
            updated_content = re.sub(re.escape(search_string), replacement_string, content)

            # Write the updated content back to the file
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(updated_content)
                print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Note location index {bubble_location_index} contents group translated per location defintion in file {os.path.basename(file_path)}.")

    except FileNotFoundError:
        print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Error: The file '{file_name}' was not found.")
    except Exception as e:
        print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: An error occurred: {e}")

    update_note_opacity(file_path, f"note-{bubble_location_index}-location", 0)

def extract_note_location(file_path, bubble_location_index):
    """
    Extracts the 'cx' and 'cy' attributes for a given note number from an SVG file.

    Args:
        file_path (str): The path to the SVG file.
        reference_number (int): The note number to search for.

    Returns:
        str: The extracted 'cx' and 'cy' attributes as a string, e.g., 'cx="192.0" cy="0.0"',
             or None if the note is not found.
    """
    start_key = f'id="bubble-location-index-{bubble_location_index}-location"'
    try:
        with open(file_path, 'r') as file:
            content = file.read()

        # Find the start index of the target string
        start_index = content.find(start_key)
        if start_index == -1:
            return None

        # Find the closing tag nearest to the start key
        end_index = content.find('/>', start_index)
        if end_index == -1:
            return None

        # Extract the substring
        substring = content[start_index:end_index]

        # Find 'cx' and 'cy' attributes
        cx_start = substring.find('cx="') + 4
        cy_start = substring.find('cy="') + 4

        if cx_start == -1 or cy_start == -1:
            return None

        cx_end = substring.find('"', cx_start)
        cy_end = substring.find('"', cy_start)

        cx_value = substring[cx_start:cx_end]
        cy_value = substring[cy_start:cy_end]

        note_coords = [cx_value, cy_value]
        return note_coords

    except FileNotFoundError:
        print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Error: File '{file_path}' not found.")
        return None
    except Exception as e:
        print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: An error occurred: {e}")
        return None

def update_note_opacity(file_path, key, opacity):
    """
    Updates the opacity attribute of an SVG <g> tag with the specified key.

    Parameters:
    file_path (str): Path to the SVG file.
    key (str): The key to search for in the <g> tag id.
    opacity (str): The new opacity value to replace with.

    Returns:
    None: The function updates the file in place.
    """
    # Define the regex pattern to find the specific <g> tag
    pattern = fr'<g id="{key}-opacity".*>'

    # Define the replacement string
    replacement = f'<g id="{key}-opacity" opacity="{opacity}">'

    try:
        # Read the SVG file content
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()

        # Check if the pattern exists in the content
        if re.search(pattern, content):
            # Replace the matching pattern with the new string
            updated_content = re.sub(pattern, replacement, content)

            # Write the updated content back to the SVG file
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(updated_content)

            print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Updated opacity for key '{key}' to {opacity} in {os.path.basename(file_path)}.")
        else:
            print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: No matching string {pattern} found in {os.path.basename(file_path)}. No changes made.")
    except FileNotFoundError:
        print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Error: The file {file_path} was not found.")
    except Exception as e:
        print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: An error occurred: {e}")

