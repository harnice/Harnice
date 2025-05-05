import os
import json
import re
from dotenv import load_dotenv
import fileio

def update_harnice_output():
    load_dotenv()

    # Load titleblock setup
    with open(fileio.path("titleblock setup"), "r", encoding="utf-8") as f:
        titleblock_setup = json.load(f)

    # Initialize attribute collection
    collected_attrs = {
        "xmlns": "http://www.w3.org/2000/svg",
        "version": "1.1",
        "font-family": "Arial",
        "font-size": "8",
        "width": "1056.0",
        "height": "816.0",
        "viewBox": "0 0 1056.0 816.0"
    }

    # Start composing the final SVG content
    svg_output = []

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
        body, attrs = extract_svg_body(tblock_svg_path)
        svg_output.append(body)
        svg_output.append('</g>')  # end tblock group

        # Subgroup: BOM
        bom_loc = attributes.get("periphery_locs", {}).get("bom_loc", [0, 0])
        translate_bom = f'translate({bom_loc[0]},{bom_loc[1]})'
        svg_output.append(f'<g id="bom" transform="{translate_bom}">')
        body, attrs = extract_svg_body(fileio.path("bom table master svg"))
        svg_output.append(body)
        svg_output.append('</g>')  # end bom group

        svg_output.append('</g>')  # end outer group

    # Compose and write final SVG
    svg_attrs_string = " ".join(f'{k}="{v}"' for k, v in collected_attrs.items())
    final_output = [f'<svg {svg_attrs_string}>'] + svg_output + ['</svg>']

    with open(fileio.path("harnice output"), "w", encoding="utf-8") as f:
        f.write('\n'.join(final_output))


def extract_svg_body(svg_path):
    if not os.path.isfile(svg_path):
        raise FileNotFoundError(f"[ERROR] SVG file not found: {svg_path}")
    with open(svg_path, "r", encoding="utf-8") as f:
        content = f.read()

    start = content.find("<svg")
    end = content.find("</svg>")
    if start == -1 or end == -1:
        raise ValueError(f"[ERROR] Malformed SVG: {svg_path}")
    body_start = content.find(">", start) + 1

    # Parse attributes from <svg ...>
    header_match = re.search(r'<svg\s+([^>]*)>', content)
    attrs = {}
    if header_match:
        for attr in re.findall(r'(\S+)="([^"]*)"', header_match.group(1)):
            key, value = attr
            attrs[key] = value

    return content[body_start:end].strip(), attrs
