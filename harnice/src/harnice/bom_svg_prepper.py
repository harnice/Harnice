import os
import csv
from os.path import basename
from inspect import currentframe
from utility import *

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
    # Construct input and output file paths using the current directory
    tsv_file_path = filepath("harness bom")
    svg_output_path = filepath("bom table master svg")

    # Columns to include in the SVG table
    selected_columns = ["Id", "Qty", "MPN"]

    # Read data from the TSV file
    table_data = read_tsv(tsv_file_path, selected_columns)

    # Replace header row with custom labels
    header_row = ["ITEM", "QTY", "MPN"]

    # Reverse the data and append the header at the end (to appear at the bottom)
    table_data = table_data[::-1]  # Reverse the rows
    table_data.append(header_row)  # Append header row at the very end

    # Generate the SVG table
    generate_svg_table(table_data, svg_output_path)

    print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: BOM SVG table saved to {svg_output_path}")

if __name__ == "__main__":
    prep_bom_svg_master()