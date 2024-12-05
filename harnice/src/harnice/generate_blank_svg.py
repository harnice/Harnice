from xml.etree.ElementTree import Element, SubElement, ElementTree, tostring
import os
from utility import delete_file, pn_from_dir, find_and_replace_svg_group, import_file_from_harnice_library
from os.path import basename
from inspect import currentframe

def create_group(svg_root, group_name, x=0, y=0, scale=1):
    """
    Creates a group structure inside the SVG root with the specified group name.
    Adds newlines, indents, and allows varying x, y, and scale for the master group.
    
    :param svg_root: The root element of the SVG.
    :param group_name: Name of the group to create.
    :param x: X translation of the master group.
    :param y: Y translation of the master group.
    :param scale: Scale factor for the master group.
    """
    # Create the master group with separate transform attributes
    master_group = SubElement(svg_root, 'g', {
        'id': f"{group_name}-master",
        'transform': f"translate({x},{y}) scale({scale})"
    })
    master_group.text = "\n    "  # Add newline and indent before subgroups

    # Create subgroups inside the master group
    subgroup_start = SubElement(master_group, 'g', {'id': f"{group_name}-master-contents-start"})
    subgroup_start.tail = "\n    "  # Add newline and indent after this subgroup

    subgroup_end = SubElement(master_group, 'g', {'id': f"{group_name}-master-contents-end"})
    subgroup_end.tail = "\n"  # Add newline after this subgroup

    # Add newline after the master group for readability
    master_group.tail = "\n"


def append_clone_use_to_svg(file_path, input_group_master_id, use_instance_name, translate_x, translate_y):
    """
    Appends a <use> element to the end of an SVG file.

    :param file_path: Path to the SVG file
    :param input_group_master_id: ID of the master group to reference
    :param use_instance_name: Name of the <use> instance
    :param translate_x: X translation for the <use> element
    :param translate_y: Y translation for the <use> element
    """
    use_element = f"""
    <use
       x="0"
       y="0"
       xlink:href="#{input_group_master_id}"
       id="{use_instance_name}"
       transform="translate({translate_x},{translate_y})" />
    """
    try:
        with open(file_path, 'r+') as svg_file:
            content = svg_file.read()
            
            # Insert before the closing </svg> tag
            if '</svg>' in content:
                content = content.replace('</svg>', f'{use_element}\n</svg>')
            else:
                # If </svg> is missing, append to the end
                content += use_element
            
            # Rewind and overwrite the file
            svg_file.seek(0)
            svg_file.write(content)
            svg_file.truncate()
        #print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Appended <use> element to {file_path}.")
    except FileNotFoundError:
        print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Error: File {file_path} not found.")
    except Exception as e:
        print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: An error occurred: {e}")


def generate_blank_svg():
    # delete old harnice output
    harnice_output_svg_filename = f"{pn_from_dir()}-harnice-output.svg"

    # Custom preamble text to be added at the beginning of the SVG file
    preamble = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg
   version="1.1"
   width="1056"
   height="816"
   id="svg1"
   sodipodi:docname="0000326128-H01-harnice-output.svg"
   inkscape:version="1.3.2 (091e20e, 2023-11-25)"
   xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape"
   xmlns:sodipodi="http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd"
   xmlns="http://www.w3.org/2000/svg"
   xmlns:svg="http://www.w3.org/2000/svg">
  <defs
     id="defs1" />
  <sodipodi:namedview
     id="namedview1"
     pagecolor="#ffffff"
     bordercolor="#000000"
     borderopacity="0.25"
     inkscape:showpageshadow="2"
     inkscape:pageopacity="0.0"
     inkscape:pagecheckerboard="0"
     inkscape:deskcolor="#d1d1d1"
     inkscape:zoom="0.37835815"
     inkscape:cx="677.9291"
     inkscape:cy="578.81665"
     inkscape:window-width="1680"
     inkscape:window-height="997"
     inkscape:window-x="0"
     inkscape:window-y="25"
     inkscape:window-maximized="0"
     inkscape:current-layer="svg1">
    <inkscape:page
       x="0"
       y="0"
       width="1056"
       height="816"
       id="page1"
       margin="0"
       bleed="0" />
    <inkscape:page
       x="1066"
       y="0"
       width="1056"
       height="816"
       id="page2"
       margin="0"
       bleed="0" />
    <inkscape:page
       x="2132"
       y="0"
       width="1056"
       height="816"
       id="page3"
       margin="0"
       bleed="0" />
  </sodipodi:namedview>"""

    # Initialize the SVG root element
    svg = Element('svg', {
        'xmlns': "http://www.w3.org/2000/svg",
        'version': "1.1",
        'width': "100",
        'height': "100"
    })

    # Add newline to the root for cleaner output
    svg.text = "\n"

    # List of group definitions with their transformation parameters
    group_definitions = [
        {'name': 'formboard', 'x': 0, 'y': 20*96, 'scale': 1},
        {'name': 'esch', 'x': 11*96, 'y': -20*96, 'scale': 0.4},
        {'name': 'bom', 'x': 22*96, 'y': -20*96, 'scale': 1.33},
        {'name': 'revision-history', 'x': -26*96, 'y': 20*96, 'scale': 1},
        {'name': 'tblock', 'x': 28*96, 'y': -20*96, 'scale': 3.78},
        {'name': 'buildnotes', 'x': 30*96, 'y': -20*96, 'scale': 1},
        {'name': 'tblock-11x8.5-border', 'x': 0, 'y': -30*96, 'scale': 3.8}
    ]

    # Add each group to the SVG with specified transformations
    for group_def in group_definitions:
        create_group(svg, group_def['name'], x=group_def['x'], y=group_def['y'], scale=group_def['scale'])

    # Specify the file path for the generated SVG
    svg_file_path = os.path.join(os.getcwd(), harnice_output_svg_filename)

    # Save the SVG structure to a file with proper formatting
    with open(svg_file_path, "wb") as file:
        # Write the custom preamble first
        file.write(preamble.encode('utf-8') + b"\n")
        # Write the SVG content (excluding the redundant root `<svg>` tag created by ElementTree)
        file.write(tostring(svg, encoding='utf-8')[22:])  # Remove redundant root `<svg>` from the ElementTree output

    print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Adding default titleblock:")
    import_file_from_harnice_library("public", "page_defaults", "library-tblock-11x8.5-border.svg")
    #find_and_replace_svg_group(target_svg_filename, source_svg_filename, group_id)
    find_and_replace_svg_group(os.path.join(os.getcwd(),harnice_output_svg_filename), os.path.join(os.getcwd(), "library_used/page_defaults/library-tblock-11x8.5-border.svg"), "tblock-11x8.5-border-master")

    print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Appending default clone uses of imported groups:")
    #append_clone_use_to_svg(file_path, input_group_master_id, use_instance_name, translate_x, translate_y)
    append_clone_use_to_svg(svg_file_path, "tblock-11x8.5-border-master", "tblock-11x8.5-border-sheet1", 0,2877.2786)
    append_clone_use_to_svg(svg_file_path, "tblock-11x8.5-border-master", "tblock-11x8.5-border-sheet2", 11*96,2877.2786)
    append_clone_use_to_svg(svg_file_path, "esch-master", "esch-sheet2", 197.89578, 2156.7381)
    append_clone_use_to_svg(svg_file_path, "bom-master", "bom-sheet1", -1495.2774,2511.3277)
    append_clone_use_to_svg(svg_file_path, "bom-master", "bom-sheet2", -439.27736,2511.3277)
    append_clone_use_to_svg(svg_file_path, "tblock-master", "tblock-sheet1", -2298.3838,2215.8197)
    append_clone_use_to_svg(svg_file_path, "tblock-master", "tblock-sheet2", -1242.3838,2215.8197)
    


    print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: New blank SVG file has been generated at: {svg_file_path}")


if __name__ == "__main__": 
    generate_blank_svg()
