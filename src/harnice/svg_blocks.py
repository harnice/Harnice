import os
import json
import re
import csv
from dotenv import load_dotenv
import fileio
import svg_utils
import component_library
from lxml import etree as ET

def update_tblocks(page_setup_contents, revhistory_data):
    for tblock_name in page_setup_contents.get("titleblocks", {}):
        tblock_data = page_setup_contents["titleblocks"].get(tblock_name)
        if not tblock_data:
            raise KeyError(f"[ERROR] Titleblock '{tblock_name}' not found in harnice output contents")

        supplier_key = tblock_data.get("supplier")
        supplier_root = os.getenv(supplier_key)
        if not supplier_root:
            raise EnvironmentError(f"[ERROR] Environment variable '{supplier_key}' is not set")

        titleblock = tblock_data.get("titleblock")

        # === Load titleblock filepaths from library ===
        attr_library_path = os.path.join(supplier_root, "titleblocks", titleblock, f"{titleblock}_attributes.json")
        svg_library_path = os.path.join(supplier_root, "titleblocks", titleblock, f"{titleblock}.svg")
        if not os.path.isfile(attr_library_path):
            raise FileNotFoundError(f"[ERROR] Attribute file not found: {attr_library_path}")
        with open(attr_library_path, "r", encoding="utf-8") as f:
            tblock_attributes = json.load(f)

        bom_loc = tblock_attributes.get("periphery_locs", {}).get("bom_loc", [0, 0])
        translate_bom = f'translate({bom_loc[0]},{bom_loc[1]})'

        # === Prepare destination path ===
        destination_svg_name = f"{fileio.partnumber('pn-rev')}.{tblock_name}_master.svg"
        destination_svg_path = os.path.join(fileio.dirpath("svg_blocks"), destination_svg_name)

        # === Build basic SVG contents ===
        svg = [
            '<?xml version="1.0" encoding="UTF-8" standalone="no"?>',
            '<svg xmlns="http://www.w3.org/2000/svg" version="1.1">',
            f'  <g id="{tblock_name}-contents-start"></g>',
            f'  <g id="{tblock_name}-contents-end"></g>',
            f'  <g id="bom" transform="{translate_bom}">',
            f'    <g id="{tblock_name}-bom-contents-start"></g>',
            f'    <g id="{tblock_name}-bom-contents-end"></g>',
            f'  </g>',
            '</svg>'
        ]

        # === Write SVG ===
        with open(destination_svg_path, "w", encoding="utf-8") as f:
            f.write("\n".join(svg))

        # === Import tblock and bom ===
        svg_utils.find_and_replace_svg_group(destination_svg_path, svg_library_path, "tblock", tblock_name)