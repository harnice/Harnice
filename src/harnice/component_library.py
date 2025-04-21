import xml.etree.ElementTree as ET
import math
import xml.dom.minidom
import os
import json
from os.path import basename
import harnice_prechecker

pn = None
rev = None

def generate_new_connector_template():
    global pn, rev
    pn = harnice_prechecker.pn_from_cwd()
    rev = harnice_prechecker.rev_from_cwd()

    if(harnice_prechecker.harnice_prechecker() == False):
        return

    #make_new_part_svg()
    make_new_part_json()

def make_new_part_json():
    attributes_blank_json = {
        "plotting_info": {
            "csys_parent_prefs": [
                ".node"
            ],
            "component_translate_inches": {
                "translate_x": 0,
                "translate_y": 0,
                "rotate_csys": 0
            }
        },
        "tooling_info": {
            "tools": []
        },
        "build_notes": [],
        "flagnote_locations": [
            {"angle": 0, "distance": 2},
            {"angle": 15, "distance": 2},
            {"angle": -15, "distance": 2},
            {"angle": 30, "distance": 2},
            {"angle": -30, "distance": 2},
            {"angle": 45, "distance": 2},
            {"angle": -45, "distance": 2},
            {"angle": 60, "distance": 2},
            {"angle": -60, "distance": 2}
        ]
    }

    attributes_blank_json_path = os.path.join(os.getcwd(), f"{pn}-attributes.json")

    if os.path.exists(attributes_blank_json_path):
        os.remove(attributes_blank_json_path)

    # Write new file
    with open(attributes_blank_json_path, "w") as json_file:
        json.dump(attributes_blank_json, json_file, indent=4)

# Function to create the root SVG element
#def make_new_part_svg():
    #create_svg()
    #add_defs()
    #add_named_view()
    #add_content()
    #save_svg()

def create_svg(width=500, height=500):
    svg = ET.Element("svg", {
        "version": "1.1",
        "id": "svg1",
        "xmlns": "http://www.w3.org/2000/svg",
        "xmlns:svg": "http://www.w3.org/2000/svg",
        "xmlns:inkscape": "http://www.inkscape.org/namespaces/inkscape",
        "xmlns:sodipodi": "http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd"
    })
    return svg

# Function to add a defs section with a rectangle and marker
def add_defs(svg):
    defs = ET.SubElement(svg, "defs", {"id": "defs1"})

    # Add rectangle
    ET.SubElement(defs, "rect", {
        "x": "197.53245",
        "y": "17.037839",
        "width": "138.96487",
        "height": "107.55136",
        "id": "rect1"
    })

    # Add marker
    marker = ET.SubElement(defs, "marker", {
        "style": "overflow:visible",
        "id": "ConcaveTriangle-80",
        "refX": "0",
        "refY": "0",
        "orient": "auto-start-reverse",
        "markerWidth": "1",
        "markerHeight": "1",
        "viewBox": "0 0 1 1"
    })
    ET.SubElement(marker, "path", {
        "transform": "scale(0.7)",
        "d": "M -2,-4 9,0 -2,4 c 2,-2.33 2,-5.66 0,-8 z",
        "style": "fill:context-stroke;fill-rule:evenodd;stroke:none",
        "id": "path7-4"
    })

# Function to add a named view
def add_named_view(svg):
    ET.SubElement(svg, "sodipodi:namedview", {
        "id": "namedview1",
        "pagecolor": "#ffffff",
        "bordercolor": "#000000",
        "borderopacity": "0.25",
        "inkscape:showpageshadow": "2",
        "inkscape:pageopacity": "0.0",
        "inkscape:deskcolor": "#d1d1d1",
    })

# Function to add content groups with parametrized buildnotes
def add_content(svg, default_bubble_locs):
    contents = ET.SubElement(svg, "g", {"id": "connector-drawing-contents-start"})

    drawing_group = ET.SubElement(contents, "g", {"id": "connector-drawing"})
    add_drawing = ET.SubElement(drawing_group, "g", {"id": "add-drawing-here"})

    # Add placeholder circle
    ET.SubElement(add_drawing, "circle", {
        "style": "fill:#000000;stroke:#000000;stroke-width:0.015;stroke-dasharray:0.18, 0.18",
        "id": "path1",
        "cx": "0",
        "cy": "0",
        "r": "10",
        "inkscape:label": "placeholder-deleteme"
    })

    contents = ET.SubElement(svg, "g", {"id": "connector-drawing-contents-end"})

# Function to save the SVG to a file
def save_svg(svg, filename):
    tree = ET.ElementTree(svg)
    # Convert the ElementTree to a string
    rough_string = ET.tostring(tree.getroot(), encoding="UTF-8")
    # Parse the string into a DOM object
    parsed = xml.dom.minidom.parseString(rough_string)
    # Pretty-print the DOM object
    pretty_svg = parsed.toprettyxml(indent="  ")
    # Write the formatted SVG to a file
    with open(filename, "w", encoding="UTF-8") as file:
        file.write(pretty_svg)

def latest_version_in_lib(domain, library_subpath, lib_name):
    """
        find the rev history tsv in the component lib
        open it
        find the row with the highest rev number
    return latest_rev_in_lib
    """

def rev_in_lib_used(domain, library_subpath, lib_name):
    """
        rev_in_lib_used = 
        is there a fileio function that returns the rev number of a directory?
        find the rev number of the directory in the library_used directory
    """

def detect_modified_files(domain, library_subpath, lib_name):
    """
    is_a_match = 
        compare all files in the library_used directory to the files in the component lib
        if all files match, return True
        if any file does not match, return False
    """

def import_library_file(domain, library_subpath, lib_file):
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

if __name__ == "__main__":
    generate_new_connector_template()