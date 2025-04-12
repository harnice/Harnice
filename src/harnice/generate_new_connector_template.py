import xml.etree.ElementTree as ET
import math
import xml.dom.minidom
import os
from os.path import basename

default_bubble_locs_polar = [
    {"bubble_location_index": "0", "location": [2, 0], "leader": [1.3, 0]},
    {"bubble_location_index": "1", "location": [2, 20], "leader": [1.3, 20]},
    {"bubble_location_index": "2", "location": [2, -20], "leader": [1.3, -20]},
    {"bubble_location_index": "3", "location": [2, 40], "leader": [1.3, 40]},
    {"bubble_location_index": "4", "location": [2, -40], "leader": [1.3, -40]},
    {"bubble_location_index": "5", "location": [2, 60], "leader": [1.3, 60]},
    {"bubble_location_index": "6", "location": [2, -60], "leader": [1.3, -60]},
    {"bubble_location_index": "7", "location": [2, 80], "leader": [1.3, 80]},
    {"bubble_location_index": "8", "location": [2, -80], "leader": [1.3, -80]},
    {"bubble_location_index": "9", "location": [2, 100], "leader": [1.3, 100]},
    {"bubble_location_index": "10", "location": [2, -100], "leader": [1.3, -100]}
]

default_bubble_locs = [None]


def polar_to_cartesian(radius, angle_deg):
    angle_rad = math.radians(angle_deg)
    x = 96* radius * math.cos(angle_rad)
    y = 96* radius * math.sin(angle_rad)
    return x, y


def default_bubble_locs_polar_to_cartesian():
    global default_bubble_locs
    default_bubble_locs = []

    for item in default_bubble_locs_polar:
        # Convert location
        polar_location = item["location"]
        cartesian_location = polar_to_cartesian(polar_location[0], polar_location[1])

        # Convert leader
        polar_leader = item["leader"]
        cartesian_leader = polar_to_cartesian(polar_leader[0], polar_leader[1])

        # Create updated dictionary
        updated_item = {
            "bubble_location_index": item["bubble_location_index"],
            "location": cartesian_location,
            "leader": cartesian_leader
        }

        default_bubble_locs.append(updated_item)

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

    for i, note in enumerate(default_bubble_locs):
        buildnote_group = ET.SubElement(contents, "g", {"id": f"bubble-location-{note['bubble_location_index']}"})
        
        bubble_location_x = note['location'][0]
        bubble_location_y = note['location'][1]
        leader_arrow_x = note['leader'][0] - bubble_location_x
        leader_arrow_y = note['leader'][1] - bubble_location_y

        circle_group = ET.SubElement(buildnote_group, "g", {"id": f"note-{note['bubble_location_index']}-location-opacity", "opacity": "1"})
        ET.SubElement(circle_group, "circle", {
            "style": "fill:#ff0000;stroke:#000000;stroke-width:0.0127855;stroke-dasharray:0.153426, 0.153426",
            "id": f"bubble-location-index-{note['bubble_location_index']}-location",
            "cx": str(bubble_location_x),
            "cy": str(bubble_location_y),
            "r": "10"
        })

        # Create the group for the path
        path_group = ET.SubElement(buildnote_group, "g", {"id": f"path-{note['bubble_location_index']}-opacity", "opacity": "1"})
        ET.SubElement(path_group, "path", {
            "style": "display:inline;fill:none;stroke:#000000;stroke-width:1px;marker-end:url(#ConcaveTriangle-80)",
            "d": f"m {bubble_location_x},{bubble_location_y} {leader_arrow_x},{leader_arrow_y}",
            "id": f"path-location-index-{note['bubble_location_index']}"
        })

        # Add translatables group
        translatables_group = ET.SubElement(buildnote_group, "g", id=f"as-printed-flagnote-{note['bubble_location_index']}-translatables")
        
        # Add contents start and end groups inside translatables group
        ET.SubElement(translatables_group, "g", id=f"as-printed-flagnote-{note['bubble_location_index']}-contents-start")
        ET.SubElement(translatables_group, "g", id=f"as-printed-flagnote-{note['bubble_location_index']}-contents-end")
    
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

def generate_connector_start_file(output_filename):
    default_bubble_locs_polar_to_cartesian()
    svg = create_svg()
    add_defs(svg)
    add_named_view(svg)
    add_content(svg, default_bubble_locs)
    save_svg(svg, output_filename)

# Main execution
if __name__ == "__main__":
    #future work: make sure you're in the right directory
        #"right directory" is undefined. maybe any directory works?
    
    parent_dir_name = f"{os.path.basename(os.getcwd())}-drawing.svg"
    print(parent_dir_name)

    generate_connector_start_file(parent_dir_name)