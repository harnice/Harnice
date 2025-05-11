import os
import json
import re
from dotenv import load_dotenv
import fileio
from lxml import etree as ET

def update_tblock_svg_block(tblock_name):
    # === Load revision row for current part/revision ===
    revision_row = {}
    if os.path.exists(fileio.path("revision history")):
        with open(fileio.path("revision history"), "r", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter="\t")
            for row in reader:
                if row.get("rev") == fileio.partnumber("R"):
                    revision_row = {k: (v or "").strip() for k, v in row.items()}
                    break

    if not revision_row:
        raise ValueError(f"[ERROR] No revision row found for rev '{fileio.partnumber('R')}' in revision history")

    # === Read Page Setup File ===
    with open(fileio.path("harnice output contents"), "r", encoding="utf-8") as f:  
        harnice_output_contents = json.load(f)

    tblock_data = harnice_output_contents.get("titleblocks", {}).get(tblock_name)
    if not tblock_data:
        raise KeyError(f"[ERROR] Titleblock '{tblock_name}' not found in harnice output contents")

    supplier = tblock_data.get("supplier")
    titleblock = tblock_data.get("titleblock")
    text_map = tblock_data.get("text_replacements", {})

    destination_svg_name = f"{fileio.partnumber('pn-rev')}.{tblock_name}_master.svg"
    destination_svg_path = os.path.join(fileio.dirpath("master_svgs"), destination_svg_name)

    # Copy the library file into editable location
    component_library.pull_file_from_lib(
        supplier,
        os.path.join("titleblocks", titleblock, f"{titleblock}.svg"),
        destination_svg_path
    )

    # Replace text in the SVG
    with open(destination_svg_path, "r", encoding="utf-8") as f:
        svg = f.read()

    for old, new in text_map.items():
        if new.startswith("pull_from_revision_history(") and new.endswith(")"):
            field_name = new[len("pull_from_revision_history("):-1]
            if field_name not in revision_row:
                raise KeyError(f"[ERROR] Field '{field_name}' not found in revision history")
            new = revision_row[field_name]
            if not new:
                raise ValueError(f"[ERROR] Field '{field_name}' is empty in revision history")

        # Handle scale lookup if the replacement is for "Scale"
        if old.lower().find("scale") != -1:
            scales_lookup = harnice_output_contents.get("scales:", {})
            if new not in scales_lookup:
                raise KeyError(f"[ERROR] Scale key '{new}' not found in scales lookup")
            new = f"{scales_lookup[new]:.3f}"

        if old not in svg:
            print(f"[WARN] key '{old}' not found in title block")

        svg = svg.replace(old, new)

    with open(destination_svg_path, "w", encoding="utf-8") as f:
        f.write(svg)