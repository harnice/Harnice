import os
import re
import xml.etree.ElementTree as ET
import csv
from utility import pn_from_dir, rotate_svg_group, find_and_replace_svg_group
from os.path import basename
from inspect import currentframe


buildnotes_filename = f"{pn_from_dir()}-buildnotes.tsv"
buildnotes_filepath = os.path.join(os.getcwd(), buildnotes_filename)

#update_flagnotes_of_connector_instance(connector_svg_path, connector_name, connector_angle)
def update_flagnotes_of_connector_instance(target_filepath, instance_name, rotation_angle):
    print("!!!!!!!!!!!!!!!!!!!!TEST BEGIN!!!!!!!!!!!!!!")
    generate_instance_flagnotes(instance_name,rotation_angle)
    add_bubble_transforms_to_flagnote_group(os.path.join(target_filepath),)
    buildnotes = find_buildnotes_of_instance(instance_name)
    instance_flagnotes_filepath = (os.path.join(os.path.dirname(target_filepath), f"{instance_name}-instance-flagnotes.svg"))
    for i in range(0, 10):
        find_and_replace_svg_group(target_filepath, instance_flagnotes_filepath, f"as-printed-bubble-note{i}")
    print("!!!!!!!!!!!!!!!!!!!!TEST END!!!!!!!!!!!!!!")

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
    
        print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: File '{buildnotes_filename}' not found. Generating a blank file.")


def find_buildnotes_of_instance(instance):
    #change this so function name is find_flagnotes and arguments are "filepath" and "instance"
    #this way you can search buildnotes, rev flagnotes, and other in the same function
    instance_buildnotes = []

    try:
        with open(buildnotes_filepath, 'r') as file:
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
        print(f"Error: The file {buildnotes_filepath} was not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

    return instance_buildnotes
    

def generate_instance_flagnotes(instance,rotation_angle):
    # Fetch build notes for the instance
    buildnotes = find_buildnotes_of_instance(instance)
    connector_flagnotes_filename = f"{instance}-instance-flagnotes.svg"
    connector_flagnotes_filepath = os.path.join(os.getcwd(), "drawing-instances", instance, connector_flagnotes_filename)

    # Ensure the directory exists
    os.makedirs(os.path.dirname(connector_flagnotes_filepath), exist_ok=True)

    # Create a new SVG file and write a basic SVG structure
    with open(connector_flagnotes_filepath, 'w') as f:
        f.write('<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="500" height="500">')

    #find all relevant pieces of info and add them to note svg as note-indices
    note_index = 0

    #to-do: add refdes as note index
    #note_index =+ 1

    #to-do: add bom item as note index
    #note_index =+ 1

    #to-do: add revs as note index
    #note_index =+ 1

    # Iterate through each build note and update the SVG
    for buildnote in buildnotes:
        # Example circle or position could be calculated here
        generate_note_svg(connector_flagnotes_filepath, "circle", buildnote, note_index)
        rotate_svg_group(connector_flagnotes_filepath, f"flagnote-circle-{buildnote}-rotatables", -1 * rotation_angle)
        note_index =+ 1


    with open(connector_flagnotes_filepath, 'a') as f:
        f.write('</svg>')



def generate_note_svg(target_file, shape, reference_number, note_index):
    """
    Generates SVG code for a specified shape and appends it to the target_file.
    Ensures proper indentation and newlines between elements for readability.
    The target_file is expected to be a valid file path string.
    """
    # Ensure the directory exists
    os.makedirs(os.path.dirname(target_file), exist_ok=True)

    # Open the file in append mode
    with open(target_file, "a") as file:
        # Start the groups
        group_start = f'\n<g id="as-printed-bubble-note{note_index}-contents-start">\n'
        file.write(group_start)

        group_start = f'\n<g id="flagnote-{shape}-{reference_number}-rotatables-contents-start">\n'
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
    id="flagnote-{shape}-{reference_number}-bubble"/>\n"""
            file.write(circle_element)

        elif shape == "triangle-up":
            triangle_up_element = f"""  
    <polygon
    points="23.73,42.93 42.93,42.93 33.33,23.73 "
    fill="#ffffff"
    stroke="#000000"
    stroke-width="0.67"
    id="flagnote-{shape}-{reference_number}-bubble"/>\n"""
            file.write(triangle_up_element)

        elif shape == "triangle-down":
            triangle_down_element = f"""
    <polygon
    points="33.33,42.93 23.73,23.73 42.93,23.73 "
    fill="#ffffff"
    stroke="#000000"
    stroke-width="0.67"
    id="flagnote-{shape}-{reference_number}-bubble"/>\n"""
            file.write(triangle_down_element)

        # Add the text element
        text_element = f"""
    <text
    x="0"
    y="3.5"
    style="font-size:9px;font-family:Arial;text-align:center;text-anchor:middle;fill:#000000;stroke-width:0.576;stroke-dasharray:none"
    id="flagnote-{shape}-{reference_number}-text">{reference_number}</text>\n"""
        file.write(text_element)

        # End the groups
        group_end = f'</g>\n<g id="flagnote-{shape}-{reference_number}-rotatables-contents-end">\n</g>\n'
        file.write(group_end)
        group_end = f'</g>\n<g id="as-printed-bubble-note{note_index}-contents-end">\n</g>\n'
        file.write(group_end)


def add_bubble_transforms_to_flagnote_group(file_path):
    for i in range (0, 10):
        note_location = extract_note_location(file_path, i)
        translate_note_group(file_path, i, note_location)
        #search svg file for string
        #replace

def translate_note_group(file_path, reference_number, note_coords):
    import re

    # Construct the search string and replacement string
    search_string = f'<g id="as-printed-bubble-note{reference_number}-translatables"/>'
    replacement_string = (
        f'<g id="as-printed-bubble-note{reference_number}-translatables" '
        f'transform="translate({note_coords[0]}, {note_coords[1]})"/>'
    )

    try:
        # Read the file content
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()

        # Replace the string
        updated_content = re.sub(re.escape(search_string), replacement_string, content)

        # Write the updated content back to the file
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(updated_content)

        print(f"Translated note group {reference_number} in {os.path.basename(file_path)}.")
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

def extract_note_location(file_path, reference_number):
    """
    Extracts the 'cx' and 'cy' attributes for a given note number from an SVG file.

    Args:
        file_path (str): The path to the SVG file.
        reference_number (int): The note number to search for.

    Returns:
        str: The extracted 'cx' and 'cy' attributes as a string, e.g., 'cx="192.0" cy="0.0"',
             or None if the note is not found.
    """
    start_key = f'id="note{reference_number}-location"'

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
        print(f"Error: File '{file_path}' not found.")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


if __name__ == "__main__":
    generate_instance_flagnotes("X1")

