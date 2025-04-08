import os
import csv
from os.path import basename
from inspect import currentframe
import utils
import file

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
