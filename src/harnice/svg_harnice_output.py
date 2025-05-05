import os
import json
from dotenv import load_dotenv
import fileio  # assumed to be your file path utility module

def update_harnice_output():

    #def update_harnice_output():
        #for each tblock in titleblocks of fileio.path("titleblock setup")
            #read file in library at location os.path.join(dotenv(supplier),"titleblocks", titleblock, f"{titleblock}_attributes.json") as attributes,
            #make a new group with id = <titleblock name>, translate <default position>
            #inside that group,
                #make a group with id = "tblock"
                    #inside that group,
                    #copy in svg contents of os.path.join(fileio.dirpath("master_svgs"),f"{titleblock name}.svg"
                #make a group with id = "bom", translate to attributes.periphery_locs.bom_loc[]
                #inside that group, 
                    #copy in svg contents of fileio.path("bom table master svg")

    load_dotenv()

    # Load titleblock setup
    with open(fileio.path("titleblock setup"), "r", encoding="utf-8") as f:
        titleblock_setup = json.load(f)

    # Start composing the final SVG content
    svg_output = ['''<svg xmlns="http://www.w3.org/2000/svg" version="1.1">''']

    for tblock_name, tblock_data in titleblock_setup.get("titleblocks", {}).items():
        # Load attributes JSON from library
        supplier = os.getenv(tblock_data.get("supplier"))
        titleblock = tblock_data.get("titleblock")
        attr_path = os.path.join(supplier, "titleblocks", titleblock, f"{titleblock}_attributes.json")
        if not os.path.isfile(attr_path):
            raise FileNotFoundError(f"[ERROR] Attribute file not found: {attr_path}")
        with open(attr_path, "r", encoding="utf-8") as f:
            attributes = json.load(f)

        # Get default position
        default_position = tblock_data.get("default_position", [0, 0])
        translate_main = f'translate({default_position[0]},{default_position[1]})'

        # Outer group for titleblock
        svg_output.append(f'<g id="{tblock_name}" transform="{translate_main}">')

        # Subgroup: tblock SVG
        svg_output.append('<g id="tblock">')
        tblock_svg_path = os.path.join(fileio.dirpath("master_svgs"), f"{fileio.partnumber("pn-rev")}.{tblock_name}_master.svg")
        svg_output.extend(extract_svg_body(tblock_svg_path))
        svg_output.append('</g>')  # end tblock group

        # Subgroup: BOM
        bom_loc = attributes.get("periphery_locs", {}).get("bom_loc", [0, 0])
        translate_bom = f'translate({bom_loc[0]},{bom_loc[1]})'
        svg_output.append(f'<g id="bom" transform="{translate_bom}">')
        svg_output.extend(extract_svg_body(fileio.path("bom table master svg")))
        svg_output.append('</g>')  # end bom group

        svg_output.append('</g>')  # end outer group

    svg_output.append('</svg>')

    # Write final SVG
    with open(fileio.path("harnice output"), "w", encoding="utf-8") as f:
        f.write('\n'.join(svg_output))


def extract_svg_body(svg_path):
    if not os.path.isfile(svg_path):
        raise FileNotFoundError(f"[ERROR] SVG file not found: {svg_path}")
    with open(svg_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Extract content between <svg ...> and </svg>
    start = content.find("<svg")
    end = content.find("</svg>")
    if start == -1 or end == -1:
        raise ValueError(f"[ERROR] Malformed SVG: {svg_path}")
    body_start = content.find(">", start) + 1
    return [content[body_start:end].strip()]