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


import json
import re
import os
import shutil
from os.path import basename
from inspect import currentframe
import fileio

wanted_tblock_libdomain = None
wanted_tblock_libsubpath = None
wanted_tblock_libfilename = None

library_used_tblock_filepath = None
json_tblock_data = None

def pull_tblock_info_from_json():
    # Load JSON json_tblock_data
    global json_tblock_data
    with open(fileio.path("tblock master text"), 'r') as jf:
        json_tblock_data = json.load(jf)

    #to-do: pull these from JSON as well
    global wanted_tblock_libdomain
    global wanted_tblock_libsubpath
    global wanted_tblock_libfilename
    wanted_tblock_libdomain = "rs"
    wanted_tblock_libsubpath = "page_defaults"
    wanted_tblock_libfilename = "rs-tblock-default.svg" 

def prep_tblock_svg_master():
    pull_tblock_info_from_json()

    global library_used_tblock_filepath
    library_used_tblock_filepath = os.path.join(os.getcwd(), "library_used", wanted_tblock_libsubpath, wanted_tblock_libfilename)

    # Grab the latest format from the library
    import_file_from_harnice_library(wanted_tblock_libdomain, wanted_tblock_libsubpath, wanted_tblock_libfilename)

    #delete existing master svg to refresh it from library-used
    if os.path.exists(fileio.path("tblock master svg")):
        os.remove(fileio.path("tblock master svg"))
        
    #move it to the svg master folder
    shutil.copy(library_used_tblock_filepath, fileio.dirpath("master_svgs"))

    #rename it to match the convention
    os.rename(os.path.join(fileio.dirpath("master_svgs"), wanted_tblock_libfilename), fileio.path("tblock master svg"))
    
    # Find info to populate into title block from the json file...

    # Read input file content
    with open(fileio.path("tblock master svg"), 'r') as inf:
        content = inf.read()

    # Replace each occurrence of "unique-id-<jsonfilefield>"
    pattern = r"tblock-key-(\w+)"
    def replacer(match):
        key = match.group(1)  # Extract the field name
        old_text = match.group(0)  # The full placeholder text
        new_text = str(json_tblock_data.get(key, old_text))  # Get replacement text or keep original
        print(f"Replacing: '{old_text}' with: '{new_text}'")  # Print the replacement info
        return new_text

    updated_content = re.sub(pattern, replacer, content)

    # Overwrite the input file with the updated content
    with open(fileio.path("tblock master svg"), 'w') as inf:
        inf.write(updated_content)
        print("Updated tblock info.")

    


if __name__ == "__main__":
    prep_tblock_svg_master()

    import os
import csv
from os.path import basename
from inspect import currentframe
import fileio

def read_tsv(file_path, columns):
    """
    Reads data from a TSV file and selects only specified columns.
    
    Args:
        file_path (str): Path to the TSV file.
        columns (list): List of column names to extract.
     
    Returns:
        list: A list of rows containing only the selected columns.
    """
    with open(file_path, 'r', newline='', encoding='utf-8') as tsv_file:
        reader = csv.DictReader(tsv_file, delimiter='\t')
        selected_data = []
        for row in reader:
            if row["Id"].isdigit():  # Only include rows with a number in the "Id" column
                selected_data.append([row[col] for col in columns])
        return selected_data

def generate_svg_table(data, output_file):
    """
    Generates an SVG table from a list of rows and saves it to a file.
    
    Args:
        data (list of lists): The table data.
        output_file (str): The path to the SVG output file.
    """
    # Column widths in inches, converted to pixels (1 inch = 96 pixels)
    column_widths = [0.375 * 96, 0.375 * 96, 2.5 * 96]
    row_height = 0.16 * 96  # Row height in pixels
    font_size = 8  # Font size in points (8pt)
    font_family = "Arial"
    line_width = 0.008 * 96  # Line width in pixels

    # Calculate the number of data rows (excluding header)
    num_data_rows = len(data) - 1  # Header is the last row in the data

    # Calculate SVG dimensions
    svg_width = sum(column_widths)
    svg_height = row_height * (num_data_rows + 1)  # Include space for header

    # Start SVG content
    svg_content = [
        f'<svg width="{svg_width}" height="{svg_height}" font-family="{font_family}" font-size="{font_size}">',
        '<g id="bom-master-contents-start">'  # Begin the "bom-master-contents-start" group
    ]

    # Add the header row
    header_row = data[-1]
    for col_index, cell in enumerate(header_row):
        x = sum(column_widths[:col_index])  # X position based on column widths
        y = 0 # Fixed Y position for the header
        cell_width = column_widths[col_index]

        # Draw cell rectangle
        svg_content.append(
            f'<rect x="{x}" y="{y - row_height}" width="{cell_width}" height="{row_height}" fill="white" stroke="black" stroke-width="{line_width}"/>'
        )

        # Format text alignment
        if col_index == 0 or col_index == 1:  # Center justify "ITEM" and "QTY"
            text_align = "text-align:center;text-anchor:middle;"
            text_x = x + cell_width / 2
        else:  # Left justify "DB PART NAME"
            text_align = "text-align:start;text-anchor:start;"
            text_x = x + 5  # Add padding for left justification

        text_y = y + row_height / 2 + 3  # Center text vertically with slight adjustment
        svg_content.append(
            f'<text x="{text_x}" y="{text_y - row_height}" fill="black" style="font-size:{font_size}px;font-family:{font_family};{text_align}" alignment-baseline="middle">{cell}</text>'
        )

    # Draw table cells
    for row_index, row in enumerate(data[:-1]):  # Exclude the header row for now
        for col_index, cell in enumerate(row):
            x = sum(column_widths[:col_index])  # X position based on column widths
            y = -1 * (1 + row_index) * row_height         # Y position based on row height
            cell_width = column_widths[col_index]

            # Draw cell rectangle
            svg_content.append(
                f'<rect x="{x}" y="{y - row_height}" width="{cell_width}" height="{row_height}" fill="white" stroke="black" stroke-width="{line_width}"/>'
            )

            # Format text alignment
            if col_index == 0 or col_index == 1:  # Center justify "ITEM" and "QTY"
                text_align = "text-align:center;text-anchor:middle;"
                text_x = x + cell_width / 2
            else:  # Left justify "DB PART NAME"
                text_align = "text-align:start;text-anchor:start;"
                text_x = x + 5  # Add padding for left justification
            
            text_y = y + row_height / 2 + 3  # Center text vertically with slight adjustment
            svg_content.append(
                f'<text x="{text_x}" y="{text_y - row_height}" fill="black" style="font-size:{font_size}px;font-family:{font_family};{text_align}" alignment-baseline="middle">{cell}</text>'
            )

            # Add a circle around values in the "ITEM" column (col_index == 0), excluding the header
            if col_index == 0:  # ITEM column
                circle_cx = x + cell_width / 2
                circle_cy = y + row_height / 2
                radius = min(cell_width, row_height) / 2 - 2  # Radius slightly smaller than cell
                svg_content.append(
                    f'<circle cx="{circle_cx}" cy="{circle_cy - row_height}" r="{radius}" fill="none" stroke="black" stroke-width="{line_width}"/>'
                )


    # Close the "bom-master-contents-start" group
    svg_content.append('</g>')

    # Add an empty group named "bom-master-contents-end"
    svg_content.append('<g id="bom-master-contents-end"></g>')

    # Close the SVG
    svg_content.append('</svg>')

    # Save SVG to file
    with open(output_file, 'w', encoding='utf-8') as svg_file:
        svg_file.write('\n'.join(svg_content))


def prep_bom_svg_master():
    # Columns to include in the SVG table
    selected_columns = ["Id", "Qty", "MPN"]

    # Read data from the TSV file
    table_data = read_tsv(fileio.path("harness bom"), selected_columns)

    # Replace header row with custom labels
    header_row = ["ITEM", "QTY", "MPN"]

    # Reverse the data and append the header at the end (to appear at the bottom)
    table_data = table_data[::-1]  # Reverse the rows
    table_data.append(header_row)  # Append header row at the very end

    # Generate the SVG table
    generate_svg_table(table_data, fileio.path("bom table master svg"))

    print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: BOM SVG table saved to {fileio.name("bom table master svg")}")

if __name__ == "__main__":
    prep_bom_svg_master()

    import os
import csv
from os.path import basename
from inspect import currentframe
import fileio

def read_tsv(file_path, columns):
    """
    Reads data from a TSV file and selects only specified columns.
    
    Args:
        file_path (str): Path to the TSV file.
        columns (list): List of column names to extract.
    
    Returns:
        list: A list of rows containing only the selected columns.
    """
    with open(file_path, 'r', newline='', encoding='utf-8') as tsv_file:
        reader = csv.DictReader(tsv_file, delimiter='\t')
        selected_data = []
        for row in reader:
            if row["Rev"].isdigit():  # Only include rows with a number in the "Rev" column
                selected_data.append([row[col] for col in columns])
        return selected_data

def generate_svg_table(data, output_file, triangle_width=14, triangle_height=12):
    """
    Generates an SVG table from a list of rows and saves it to a file.
    
    Args:
        data (list of lists): The table data.
        output_file (str): The path to the SVG output file.
        triangle_width (int): The width of the upside-down triangle.
        triangle_height (int): The height of the upside-down triangle.
    """
    # Column widths in inches, converted to pixels (1 inch = 96 pixels)
    column_widths = [0.375 * 96, 0.6 * 96, 0.8 * 96, 2.5 * 96]
    row_height = 0.16 * 96  # Row height in pixels
    font_size = 8  # Font size in points (8pt)
    font_family = "Arial"
    line_width = 0.008 * 96  # Line width in pixels

    # Calculate SVG dimensions
    svg_width = sum(column_widths)
    svg_height = row_height * len(data)

    # Start SVG content
    svg_content = [
        f'<svg width="{svg_width}" height="{svg_height}" font-family="{font_family}" font-size="{font_size}">', 
        '<g id="revision-history-master-contents-start">'  # Begin the "bom-master-contents-start" group
    ]

    # Draw table cells
    for row_index, row in enumerate(data):
        for col_index, cell in enumerate(row):
            x = sum(column_widths[:col_index])  # X position based on column widths
            y = row_index * row_height         # Y position based on row height
            cell_width = column_widths[col_index]

            # Draw cell rectangle
            svg_content.append(
                f'<rect x="{x}" y="{y}" width="{cell_width}" height="{row_height}" fill="white" stroke="black" stroke-width="{line_width}"/>'
            )

            # Format text alignment
            if col_index == 0 or col_index == 1:  # Center justify "ITEM" and "QTY"
                text_align = "text-align:center;text-anchor:middle;"
                text_x = x + cell_width / 2
            else:  # Left justify "DB PART NAME"
                text_align = "text-align:start;text-anchor:start;"
                text_x = x + 5  # Add padding for left justification

            text_y = y + row_height / 2 + 3  # Center text vertically with slight adjustment
            svg_content.append(
                f'<text x="{text_x}" y="{text_y}" fill="black" style="font-size:{font_size}px;font-family:{font_family};{text_align}" alignment-baseline="middle">{cell}</text>'
            )

            # Add an upside-down triangle around numerical "Rev" values
            if col_index == 0 and row_index != 0:  # Only for the first column, excluding the header
                try:
                    if cell.isdigit():  # Check if the cell contains a numerical value
                        triangle_base_x = x + cell_width / 2
                        triangle_tip_y = y + row_height / 2 + triangle_height / 2
                        triangle_bottom_y = y + row_height / 2 - triangle_height / 2
                        triangle_points = [
                            (triangle_base_x, triangle_tip_y),  # Tip of the triangle
                            (triangle_base_x - triangle_width / 2, triangle_bottom_y),  # Bottom-left
                            (triangle_base_x + triangle_width / 2, triangle_bottom_y)   # Bottom-right
                        ]
                        points_attribute = " ".join(f"{px},{py}" for px, py in triangle_points)
                        svg_content.append(
                            f'<polygon points="{points_attribute}" fill="none" stroke="black" stroke-width="{line_width}"/>'
                        )
                except AttributeError:
                    pass  # If the cell value is not a string, ignore it

    # Close the "bom-master-contents-start" group
    svg_content.append('</g>')

    # Add an empty group named "bom-master-contents-end"
    svg_content.append('<g id="revision-history-master-contents-end"></g>')

    # Close the SVG
    svg_content.append('</svg>')

    # Save SVG to file
    with open(output_file, 'w', encoding='utf-8') as svg_file:
        svg_file.write('\n'.join(svg_content))


if __name__ == "__main__":
    # Directory containing this script
    current_directory = os.getcwd()

    # Input TSV file path
    tsv_file_path = os.path.join(current_directory, "revision-history.tsv")

    # Output SVG file path
    svg_output_path = os.path.join(current_directory, "revision-history.svg")

    # Columns to include in the SVG table
    selected_columns = ["Rev", "Date", "Drawn By", "Desc"]

    # Read data from the TSV file
    table_data = read_tsv(tsv_file_path, selected_columns)

    # Replace header row with custom labels
    header_row = ["REV", "DATE", "DRAWN BY", "DESCRIPTION"]
    table_data.insert(0, header_row)  # Insert header row at the very beginning

    # Generate the SVG table
    generate_svg_table(table_data, svg_output_path)

    print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: SVG table saved to {svg_output_path}")

import os
from os.path import basename
from inspect import currentframe
import fileio
import svg_utils

def regen_harnice_output_svg():

    # Perform the find-and-replace operations using the dynamically generated filenames
    svg_utils.find_and_replace_svg_group(fileio.path("harnice output"), fileio.path("formboard master svg"), "formboard-master")
    print()
    svg_utils.find_and_replace_svg_group(fileio.path("harnice output"), fileio.path("bom table master svg"), "bom-master")
    print()
    svg_utils.find_and_replace_svg_group(fileio.path("harnice output"), fileio.path("revhistory master svg"), "revision-history-master")
    print()
    svg_utils.find_and_replace_svg_group(fileio.path("harnice output"), fileio.path("tblock master svg"), "tblock-master")
    print()
    svg_utils.find_and_replace_svg_group(fileio.path("harnice output"), fileio.path("buildnotes master svg"), "buildnotes-master")
    print()
    svg_utils.find_and_replace_svg_group(fileio.path("harnice output"), fileio.path("esch master svg"), "esch-master")
    print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: No more replacements.")

if __name__ == "__main__":
    regen_harnice_output_svg()