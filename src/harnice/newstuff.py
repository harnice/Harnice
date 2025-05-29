import os
import json
import xml.etree.ElementTree as ET
from dotenv import load_dotenv, dotenv_values
import os
import xml.etree.ElementTree as ET
from xml.dom import minidom
from harnice import(
    rev_history,
    cli,
    fileio,
)
from harnice.commands import render

def part(library, mfgmpn):
    load_dotenv()

    library_path = os.getenv(library)
    if not library_path:
        raise ValueError(
            f"Environment variable '{library}' is not set. Add the path to this library from your harnice root directory."
        )

    part_directory = os.path.join(library_path, "parts", mfgmpn)

    if os.path.exists(part_directory):
        if cli.prompt("File already exists. Do you want to remove it?", "no") == "no":
            print("Exiting harnice")
            exit()
        else:
            import shutil
            shutil.rmtree(part_directory)
    
    os.makedirs(part_directory)

    cwd = os.getcwd()
    os.chdir(part_directory)
    #fileio.verify_revision_structure()

    #======== MAKE NEW PART JSON ===========
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
            {"angle": 0, "distance": 2, "arrowhead_angle": "", "arrowhead_distance": 1},
            {"angle": 15, "distance": 2, "arrowhead_angle": "", "arrowhead_distance": 1},
            {"angle": -15, "distance": 2, "arrowhead_angle": "", "arrowhead_distance": 1},
            {"angle": 30, "distance": 2, "arrowhead_angle": "", "arrowhead_distance": 1},
            {"angle": -30, "distance": 2, "arrowhead_angle": "", "arrowhead_distance": 1},
            {"angle": 45, "distance": 2, "arrowhead_angle": "", "arrowhead_distance": 1},
            {"angle": -45, "distance": 2, "arrowhead_angle": "", "arrowhead_distance": 1},
            {"angle": 60, "distance": 2, "arrowhead_angle": "", "arrowhead_distance": 1},
            {"angle": -60, "distance": 2, "arrowhead_angle": "", "arrowhead_distance": 1},
            {"angle": -75, "distance": 2, "arrowhead_angle": "", "arrowhead_distance": 1},
            {"angle": 75, "distance": 2, "arrowhead_angle": "", "arrowhead_distance": 1},
            {"angle": -90, "distance": 2, "arrowhead_angle": "", "arrowhead_distance": 1},
            {"angle": 90, "distance": 2, "arrowhead_angle": "", "arrowhead_distance": 1},
            {"angle": -105, "distance": 2, "arrowhead_angle": "", "arrowhead_distance": 1},
            {"angle": 105, "distance": 2, "arrowhead_angle": "", "arrowhead_distance": 1},
            {"angle": -120, "distance": 2, "arrowhead_angle": "", "arrowhead_distance": 1},
        ]
    }

    attributes_blank_json_path = os.path.join(fileio.rev_directory(), f"{mfgmpn}-attributes.json")

    if os.path.exists(attributes_blank_json_path):
        os.remove(attributes_blank_json_path)

    with open(attributes_blank_json_path, "w") as json_file:
        json.dump(attributes_blank_json, json_file, indent=4)

    #======== MAKE NEW PART SVG ===========
    svg_width = 400
    svg_height = 400

    # === SVG Init ===
    svg = ET.Element('svg', {
        "xmlns": "http://www.w3.org/2000/svg",
        "version": "1.1",
        "width": str(svg_width),
        "height": str(svg_height),
    })

    # === Group Start ===
    contents_group = ET.SubElement(svg, "g", {"id": "tblock-contents-start"})

    # === Rectangle ===
    ET.SubElement(contents_group, "rect", {
        "x": str(0),
        "y": str(-48),
        "width": str(96),
        "height": str(96),
        "fill": "#ccc",
        "stroke": "black",
        "stroke-width": "1"
    })

    # === Group End ===
    ET.SubElement(svg, "g", {"id": "tblock-contents-end"})

    # === Write SVG ===
    rough_string = ET.tostring(svg, encoding="utf-8")
    pretty = minidom.parseString(rough_string).toprettyxml(indent="  ")
    attributes_blank_json_path = os.path.join(fileio.rev_directory(), f"{mfgmpn}-drawing.svg")

    with open(attributes_blank_json_path, "w", encoding="utf-8") as f:
        f.write(pretty)

    # === Write attributes file ===
    periphery_json = {
        "periphery_locs": {
            "bom_loc": [tb_origin_x, tb_origin_y]  # same as bottom-left of titleblock
        },
        "page_size_in": [
            round(p["page_size"][0] / 96, 3),
            round(p["page_size"][1] / 96, 3)
        ]
    }

    periphery_path = os.path.join(fileio.rev_directory(), f"{name}.attributes.json")
    with open(periphery_path, "w", encoding="utf-8") as f:
        json.dump(periphery_json, f, indent=2)

    os.chdir(cwd)


def tblock(library, name):
    load_dotenv()

    library_path = os.getenv(library)
    if not library_path:
        raise ValueError(
            f"Environment variable '{library}' is not set. Add the path to this library from your harnice root directory."
        )

    tblock_directory = os.path.join(library_path, "titleblocks", name)

    if os.path.exists(tblock_directory):
        if cli.prompt("File already exists. Do you want to remove it?", "no") == "no":
            print("Exiting harnice")
            exit()
        else:
            import shutil
            shutil.rmtree(tblock_directory)
    
    os.makedirs(os.path.join(tblock_directory, f"{name}-rev1"))

    cwd = os.getcwd()
    os.chdir(tblock_directory)

    param_path = os.path.join(tblock_directory, f"{name}-rev1", f"{name}-rev1.params.json")
    svg_path = os.path.join(tblock_directory, f"{name}-rev1", f"{name}-rev1.params.json")

    # === Default Parameters ===
    params = {
        "page_size": [11 * 96, 8.5 * 96],
        "outer_margin": 20,
        "inner_margin": 40,
        "tick_spacing": 96,
        "tb_origin_offset": [398, 48],
        "row_heights": [24, 24],
        "column_widths": [
            [264, 50, 84],
            [73, 126, 139, 60]
        ],
        "label_offset": [2, 7],
        "key_offset_y": 16,
        "cell_texts": [
            [("DESCRIPTION", "tblock-key-desc"), ("REV", "tblock-key-rev"), ("RELEASE TICKET", "tblock-key-releaseticket")],
            [("SCALE", "tblock-key-scale"), ("PART NUMBER", "tblock-key-pn"),
             ("DRAWN BY", "tblock-key-drawnby"), ("SHEET", "tblock-key-sheet")]
        ]
    }

    # === If param file doesn't exist, create it ===
    if not os.path.exists(param_path):
        with open(param_path, "w", encoding="utf-8") as f:
            json.dump(params, f, indent=2)

    # === carry out the rest in render ===
    render.tblock()

    # === switch back to wherever you were before ===
    os.chdir(cwd)