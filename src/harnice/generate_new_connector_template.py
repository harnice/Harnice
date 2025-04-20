import xml.etree.ElementTree as ET
import math
import xml.dom.minidom
import os
from os.path import basename

# Main execution
if __name__ == "__main__":
    #future work: make sure you're in the right directory
        #"right directory" is undefined. maybe any directory works?
    
    parent_dir_name = f"{os.path.basename(os.getcwd())}-drawing.svg"
    
    #print(parent_dir_name)
    #svg = create_svg()
    #add_defs(svg)
    #add_named_view(svg)
    #add_content(svg, default_bubble_locs)
    #save_svg(svg, output_filename)

default_bubble_locs = [None]

# Function to create the root SVG element
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