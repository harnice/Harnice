import os
import json
import xml.etree.ElementTree as ET
from xml.dom import minidom
from harnice import (
    run_wireviz,
    wirelist,
    instances_list,
    svg_utils,
    flagnotes,
    formboard,
    rev_history,
    component_library,
    fileio,
    svg_outputs
)

def harness():
    print("Thanks for using Harnice!")
    
    #=============== CHECK REVISION HISTORY #===============
    fileio.verify_revision_structure()
        #reads file structure and revision history tsv if exists
        #writes a new revision history document if else
    #TODO: make sure there's a yaml in the rev folder or generate a blank one?

    #=============== GENERATE FILE STRUCTURE #===============
    fileio.generate_structure()
        #completely deletes everything in support_do_not_edit
        #makes sure all the directories exist

    #=============== INITIALIZE INSTANCES LIST #===============
    #make a list of every single instance in the project

    instances_list.make_new_list()
        #makes blank document
    instances_list.add_connectors()
        #adds connectors from the yaml to that document
    instances_list.add_cables()
        #adds cables from the yaml to that document
    wirelist.newlist()
        #makes a new wirelist

    #=============== CHECKING COMPONENTS AGAINST LIBRARY #===============
    component_library.pull_parts()
        #compares existing imported library files against library
        #imports new files if they don't exist
        #if they do exist,
        #checks for updates against the library
        #checks for modifications against the library

    #=============== PRODUCING A FORMBOARD BASED ON DEFINED ESCH #===============
    instances_list.generate_nodes_from_connectors()
        #makes at least one node per connector, named the same as connectors for now

    instances_list.update_parent_csys()
        #updates parent csys of each connector based on its definition json

    instances_list.update_component_translate()
        #updates translations of any kind of instance with respect to its csys

    #make a formboard definition file from scratch if it doesn't exist
    if not os.path.exists(fileio.name("formboard graph definition")):
        with open(fileio.name("formboard graph definition"), 'w') as f:
            pass  # Creates an empty file

    formboard.validate_nodes()
    instances_list.add_nodes_from_formboard()
    instances_list.add_segments_from_formboard()
        #validates all nodes exist
        #generates segments if they don't exist
        #adds nodes and segments into the instances list

    print()
    print("Validating your formboard graph is structured properly...")
    formboard.map_cables_to_segments()
    formboard.detect_loops()
    formboard.detect_dead_segments()
        #validates segments are structured correctly

    formboard.generate_node_coordinates()
        #starting from one node, recursively find lengths and angles of related segments to produce locations of each node

    instances_list.add_cable_lengths()
    wirelist.add_lengths()
        #add cable lengths to instances and wirelists

    wirelist.tsv_to_xls()
        #now that wirelist is complete, make it pretty

    instances_list.add_absolute_angles_to_segments()
        #add absolute angles to segments only such that they show up correctly on formboard
        #segments only, because every other instance angle is associated with its parent node
        #segments have by defintiion more than one node, so there's no easy way to resolve segment angle from that
    instances_list.add_angles_to_nodes()
        #add angles to nodes to base the rotation of each node child instance

    #=============== GENERATING A BOM #===============
    instances_list.convert_to_bom()
        #condenses an instance list down into a bom
    instances_list.add_bom_line_numbers()
        #adds bom line numbers back to the instances list

    #=============== HANDLING FLAGNOTES #===============
    instances_list_data = instances_list.read_instance_rows()
    rev_history_data = rev_history.revision_info()
    buildnotes_data = ""

    flagnotes.create_flagnote_matrix_for_all_instances(instances_list_data)

    flagnotes.add_flagnote_content(
        flagnotes.read_flagnote_matrix_file(),
        instances_list_data,
        rev_history_data,
        buildnotes_data
    )

    instances_list.add_flagnotes(
        flagnotes.read_flagnote_matrix_file()
    )

    #=============== RUNNING WIREVIZ #===============
    run_wireviz.generate_esch()

    #=============== REBUILDING OUTPUT SVG #===============
    page_setup_contents = svg_outputs.update_page_setup_json()
        #ensure page setup is defined, if not, make a basic one
    revinfo = rev_history.revision_info()

    #prepare the building blocks as svgs
    svg_outputs.prep_formboard_drawings(page_setup_contents)
    svg_outputs.prep_wirelist()
    svg_outputs.prep_bom()
    #esch done under run_wireviz.generate_esch()
    svg_outputs.prep_tblocks(page_setup_contents, revinfo)

    svg_outputs.prep_master(page_setup_contents)
        #merges all building blocks into one main support_do_not_edit master svg file

    svg_outputs.update_harnice_output(page_setup_contents)
        #adds the above to the user-editable svgs in page setup, one per page

    svg_utils.produce_multipage_harnice_output_pdf(page_setup_contents)
        #makes a PDF out of each svg in page setup

def tblock():
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

    fileio.verify_revision_structure()

    # === If param file doesn't exist, create it ===
    if not os.path.exists(fileio.path("params")):
        with open(fileio.path("params"), "w", encoding="utf-8") as f:
            json.dump(params, f, indent=2)
        #if it does exist, ignore it

    # === Load parameters from JSON ===
    with open(fileio.path("params"), "r", encoding="utf-8") as f:
        p = json.load(f)

    width, height = p["page_size"]
    svg = ET.Element('svg', {
        "xmlns": "http://www.w3.org/2000/svg",
        "version": "1.1",
        "width": str(width),
        "height": str(height)
    })

    contents_group = ET.SubElement(svg, "g", {"id": "tblock-contents-start"})

    def add_rect(parent, x, y, w, h, stroke="black", fill="none", stroke_width=1):
        ET.SubElement(parent, "rect", {
            "x": str(x),
            "y": str(y),
            "width": str(w),
            "height": str(h),
            "fill": fill,
            "stroke": stroke,
            "stroke-width": str(stroke_width)
        })

    def add_text(parent, x, y, text, size=8, anchor="start", bold=False, id=None):
        style = f"font-size:{size}px;font-family:Arial"
        if bold:
            style += ";font-weight:bold"
        attrs = {
            "x": str(x),
            "y": str(y),
            "style": style,
            "text-anchor": anchor,
        }
        if id:
            attrs["id"] = id
        ET.SubElement(parent, "text", attrs).text = text

    # === Border Group ===
    border_group = ET.SubElement(contents_group, "g", {"id": "border"})

    x_ticks = int((width - 2 * p["inner_margin"]) // p["tick_spacing"])
    for i in range(x_ticks):
        x0 = p["inner_margin"] + i * p["tick_spacing"]
        x_center = x0 + p["tick_spacing"] / 2
        ET.SubElement(border_group, "line", {
            "x1": str(x0), "y1": str(p["outer_margin"]),
            "x2": str(x0), "y2": str(height - p["outer_margin"]),
            "stroke": "black", "stroke-width": "0.5"
        })
        label_y_top = (p["outer_margin"] + p["inner_margin"]) / 2
        label_y_bot = height - label_y_top
        add_text(border_group, x_center, label_y_top, str(i + 1), anchor="middle")
        add_text(border_group, x_center, label_y_bot, str(i + 1), anchor="middle")

    x_end = p["inner_margin"] + x_ticks * p["tick_spacing"]
    ET.SubElement(border_group, "line", {
        "x1": str(x_end), "y1": str(p["outer_margin"]),
        "x2": str(x_end), "y2": str(height - p["outer_margin"]),
        "stroke": "black", "stroke-width": "0.5"
    })

    y_ticks = int((height - 2 * p["inner_margin"]) // p["tick_spacing"])
    for j in range(y_ticks):
        y0 = p["inner_margin"] + j * p["tick_spacing"]
        y_center = y0 + p["tick_spacing"] / 2
        ET.SubElement(border_group, "line", {
            "x1": str(p["outer_margin"]), "y1": str(y0),
            "x2": str(width - p["outer_margin"]), "y2": str(y0),
            "stroke": "black", "stroke-width": "0.5"
        })
        label = chr(ord('A') + j)
        label_x_left = (p["outer_margin"] + p["inner_margin"]) / 2
        label_x_right = width - label_x_left
        add_text(border_group, label_x_left, y_center + 4, label, anchor="middle")
        add_text(border_group, label_x_right, y_center + 4, label, anchor="middle")

    y_end = p["inner_margin"] + y_ticks * p["tick_spacing"]
    ET.SubElement(border_group, "line", {
        "x1": str(p["outer_margin"]), "y1": str(y_end),
        "x2": str(width - p["outer_margin"]), "y2": str(y_end),
        "stroke": "black", "stroke-width": "0.5"
    })

    add_rect(border_group, p["outer_margin"], p["outer_margin"], width - 2 * p["outer_margin"], height - 2 * p["outer_margin"])
    add_rect(border_group, p["inner_margin"], p["inner_margin"], width - 2 * p["inner_margin"], height - 2 * p["inner_margin"], stroke="black", fill="white", stroke_width=1)

    # === Logo Group ===
    tb_origin_x = width - p["inner_margin"] - p["tb_origin_offset"][0]
    tb_origin_y = height - p["inner_margin"] - p["tb_origin_offset"][1]
    logo_width = 1.25 * 96
    logo_height = sum(p["row_heights"])
    logo_group = ET.SubElement(contents_group, "g", {"id": "logo"})
    add_rect(logo_group, tb_origin_x - logo_width, tb_origin_y, logo_width, logo_height)

    # === Titleblock Cell Groups ===
    y_cursor = tb_origin_y
    for row_idx, row_height in enumerate(p["row_heights"]):
        row_cols = p["column_widths"][row_idx]
        row_cells = p["cell_texts"][row_idx]
        x_cursor = tb_origin_x
        for col_idx, col_width in enumerate(row_cols):
            label, key_id = row_cells[col_idx]
            group_id = label.lower().replace(" ", "-") if label else f"cell-r{row_idx}-c{col_idx}"
            cell_group = ET.SubElement(contents_group, "g", {"id": group_id})
            add_rect(cell_group, x_cursor, y_cursor, col_width, row_height)

            if label:
                add_text(cell_group,
                         x_cursor + p["label_offset"][0],
                         y_cursor + p["label_offset"][1],
                         label, size=7, bold=True)
            if key_id:
                center_x = x_cursor + col_width / 2
                add_text(cell_group,
                         center_x,
                         y_cursor + p["key_offset_y"],
                         key_id, size=7, anchor="middle", id=key_id)

            x_cursor += col_width
        y_cursor += row_height

    ET.SubElement(svg, "g", {"id": "tblock-contents-end"})
    rough_string = ET.tostring(svg, encoding="utf-8")
    pretty = minidom.parseString(rough_string).toprettyxml(indent="  ")
    with open(fileio.path("drawing"), "w", encoding="utf-8") as f:
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

    with open(fileio.path("attributes"), "w", encoding="utf-8") as f:
        json.dump(periphery_json, f, indent=2)

def part():
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

    fileio.verify_revision_structure()

    if os.path.exists(fileio.path("attributes")):
        os.remove(fileio.path("attributes"))

    with open(fileio.path("attributes"), "w") as json_file:
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

    with open(fileio.path("drawing"), "w", encoding="utf-8") as f:
        f.write(pretty)

def flagnote():
    params = {
        "vertices": [
            [-19.2, -19.2],
            [ 19.2, -19.2],
            [ 19.2,  19.2],
            [-19.2,  19.2]
        ],
        "fill": 0xFFFFFF,
        "border": 0x000000,
        "text inside": "flagnote-text"
    }

    fileio.verify_revision_structure()

    # === If param file doesn't exist, create it ===
    if not os.path.exists(fileio.path("params")):
        with open(fileio.path("params"), "w", encoding="utf-8") as f:
            json.dump(params, f, indent=2)

    # === Load parameters from JSON ===
    with open(fileio.path("params"), "r", encoding="utf-8") as f:
        p = json.load(f)

    svg = ET.Element('svg', {
        "xmlns": "http://www.w3.org/2000/svg",
        "version": "1.1",
        "width": str(6 * 96),
        "height": str(6 * 96)
    })

    contents_group = ET.SubElement(svg, "g", {"id": "flagnote-contents-start"})

    # === Add polygon from vertex list ===
    if p["vertices"]:
        points_str = " ".join(f"{x},{y}" for x, y in p["vertices"])
        ET.SubElement(contents_group, "polygon", {
            "points": points_str,
            "fill": f"#{p['fill']:06X}",
            "stroke": f"#{p['border']:06X}"
        })

    # === Add label at (0, 0) centered ===
    style = "font-size:8px;font-family:Arial"
    attrs = {
        "x": "0",
        "y": "0",
        "style": style,
        "text-anchor": "middle",
        "dominant-baseline": "middle",
        "id": "flagnote-text"
    }
    ET.SubElement(contents_group, "text", attrs).text = p.get("text inside", "")

    ET.SubElement(svg, "g", {"id": "flagnote-contents-end"})

    rough_string = ET.tostring(svg, encoding="utf-8")
    pretty = minidom.parseString(rough_string).toprettyxml(indent="  ")
    with open(fileio.path("drawing"), "w", encoding="utf-8") as f:
        f.write(pretty)

def system():
    print("System-level rendering not yet implemented.")