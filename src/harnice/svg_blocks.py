import os
import json
import re
import csv
from dotenv import load_dotenv
import fileio
import component_library
from lxml import etree as ET

def update_tblocks(page_setup_contents, revhistory_data):
    for tblock_name in page_setup_contents.get("titleblocks", {}):

        tblock_data = page_setup_contents.get("titleblocks", {}).get(tblock_name)
        if not tblock_data:
            raise KeyError(f"[ERROR] Titleblock '{tblock_name}' not found in harnice output contents")

        supplier = tblock_data.get("supplier")
        titleblock = tblock_data.get("titleblock")
        text_map = tblock_data.get("text_replacements", {})

        destination_svg_name = f"{fileio.partnumber('pn-rev')}.{tblock_name}_master.svg"
        destination_svg_path = os.path.join(fileio.dirpath("svg_blocks"), destination_svg_name)

        # === Copy the library file to master SVGs ===
        component_library.pull_file_from_lib(
            supplier,
            os.path.join("titleblocks", titleblock, f"{titleblock}.svg"),
            destination_svg_path
        )

        # === Perform Text Replacements ===
        with open(destination_svg_path, "r", encoding="utf-8") as f:
            svg = f.read()

        for old, new in text_map.items():
            if new.startswith("pull_from_revision_history(") and new.endswith(")"):
                field_name = new[len("pull_from_revision_history("):-1]
                value = revhistory_data.get(field_name, "").strip()

                if not value:
                    raise ValueError(f"[ERROR] Field '{field_name}' is missing or empty in revision history")

                new = value

            # If replacing scale, convert to decimal
            if "scale" in old.lower():
                scales_lookup = page_setup_contents.get("scales:", {})
                if new not in scales_lookup:
                    raise KeyError(f"[ERROR] Scale key '{new}' not found in scales lookup")
                new = f"{scales_lookup[new]:.3f}"

            if old not in svg:
                print(f"[WARN] Key '{old}' not found in titleblock SVG")

            svg = svg.replace(old, new)

        # === Build contents for support_do_not_edit-contents_start group ===
        tblock_attr_path = os.path.join(os.getenv(supplier), "titleblocks", titleblock, f"{titleblock}_attributes.json")
        if not os.path.isfile(tblock_attr_path):
            raise FileNotFoundError(f"[ERROR] Attribute file not found: {tblock_attr_path}")
        with open(tblock_attr_path, "r", encoding="utf-8") as f:
            tblock_attributes = json.load(f)

        # BOM group
        bom_loc = tblock_attributes.get("periphery_locs", {}).get("bom_loc", [0, 0])
        translate_bom = f'translate({bom_loc[0]},{bom_loc[1]})'
        svg.append(f'<g id="bom" transform="{translate_bom}">')
        svg.append(f'<g id="{tblock_name}-bom-contents-start"></g>')
        svg.append(f'<g id="{tblock_name}-bom-contents-end"></g>')
        svg.append('</g>')

        group.append('</g>')  # End outer titleblock group
        inner_groups.append("\n".join(group))

        with open(destination_svg_path, "w", encoding="utf-8") as f:
            f.write(svg)
