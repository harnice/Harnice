import os
import json
import subprocess
from harnice import fileio, rev_history, component_library, svg_utils

artifact_mpn = "pdf_generator"

#=============== PATHS ===============
def path(target_value):
    #artifact_path gets passed in as a global from the caller
    if target_value == "page setup":
        return os.path.join(artifact_path, f"{fileio.partnumber("pn-rev")}-page_setup.json")
    if target_value == "output pdf":
        return os.path.join(artifact_path, f"{fileio.partnumber("pn-rev")}-{artifact_id}-output.pdf")
    if target_value == "master contents":
        return os.path.join(artifact_path, f"{fileio.partnumber("pn-rev")}-{artifact_id}-mastercontents.svg")
    if target_value == "page svgs":
        os.makedirs(os.path.join(artifact_path, "page_svgs"), exist_ok=True)
        return os.path.join(artifact_path, "page_svgs")
    if target_value == "tblock svgs":
        os.makedirs(os.path.join(artifact_path, "tblock_svgs"), exist_ok=True)
        return os.path.join(artifact_path, "tblock_svgs")
    else:
        raise KeyError(f"Filename {target_value} not found in {artifact_mpn} file tree")

def update_page_setup_json():
    """Ensure page setup JSON exists and return its contents."""

    # Default Titleblock Setup
    blank_setup = {
        "pages": [
            {
                "name": "page1",
                "supplier": "public",
                "titleblock": "harnice_tblock-11x8.5",
                "text_replacements": {
                    "tblock-key-desc": "pull_from_revision_history(desc)",
                    "tblock-key-pn": "pull_from_revision_history(pn)",
                    "tblock-key-drawnby": "pull_from_revision_history(drawnby)",
                    "tblock-key-rev": "pull_from_revision_history(rev)",
                    "tblock-key-releaseticket": "",
                    "tblock-key-scale": "A",
                    "tblock-key-sheet": "autosheet"
                },
                "show_items": [] #"bom", "buildnotes", "revhistory"
            }
        ]
    }

    # Create or load the page setup file
    if not os.path.exists(path("page setup")) or os.path.getsize(path("page setup")) == 0:
        page_data = blank_setup
    else:
        try:
            with open(path("page setup"), "r", encoding="utf-8") as f:
                page_data = json.load(f)
        except json.JSONDecodeError:
            page_data = blank_setup

    # Always write back a valid version
    with open(path("page setup"), "w", encoding="utf-8") as f:
        json.dump(page_data, f, indent=4)

    return page_data

def prep_tblocks(page_setup_contents, revhistory_data):
    # === Validate page name uniqueness ===
    page_names = [p.get("name") for p in page_setup_contents.get("pages", [])]
    duplicates = {name for name in page_names if page_names.count(name) > 1}
    if duplicates:
        raise ValueError(f"[ERROR] Duplicate page name(s) found: {', '.join(duplicates)}")

    for page in page_setup_contents.get("pages", []):
        page_name = page.get("name")
        tblock_data = page  # each item in the list *is* the tblock_data
        if not tblock_data:
            raise KeyError(f"[ERROR] Titleblock '{page_name}' not found in harnice output contents")

        supplier_key = tblock_data.get("supplier")
        supplier_root = os.getenv(supplier_key)
        if not supplier_root:
            raise EnvironmentError(f"[ERROR] Environment variable '{supplier_key}' is not set")

        titleblock = tblock_data.get("titleblock")

        # === Prepare destination directory for used files ===
        destination_directory = os.path.join(path("tblock svgs"), page_name)

        # === Pull from library ===
        component_library.pull_item_from_library(
            supplier=supplier_key,
            lib_subpath="titleblocks",
            mpn=titleblock,
            destination_directory=destination_directory,
            used_rev=None,
            item_name=titleblock
        )

        # === Access pulled files ===
        attr_path = os.path.join(destination_directory, f"{page_name}-attributes.json")
        os.rename(os.path.join(destination_directory,f"{titleblock}-attributes.json"), attr_path)
        svg_path = os.path.join(destination_directory, f"{titleblock}.svg")

        if not os.path.isfile(attr_path):
            raise FileNotFoundError(f"[ERROR] Attribute file not found: {attr_path}")
        with open(attr_path, "r", encoding="utf-8") as f:
            tblock_attributes = json.load(f)

        # === Page size in pixels ===
        page_size_in = tblock_attributes.get("page_size_in", [11, 8.5])
        page_size_px = [int(page_size_in[0] * 96), int(page_size_in[1] * 96)]

        bom_loc = tblock_attributes.get("periphery_locs", {}).get("bom_loc", [0, 0])
        translate_bom = f'translate({bom_loc[0]},{bom_loc[1]})'

        buildnotes_loc = tblock_attributes.get("periphery_locs", {}).get("buildnotes_loc", [0, 0])
        translate_buildnotes = f'translate({buildnotes_loc[0]},{buildnotes_loc[1]})'

        revhistory_loc = tblock_attributes.get("periphery_locs", {}).get("revhistory_loc", [0, 0])
        translate_revhistory = f'translate({revhistory_loc[0]},{revhistory_loc[1]})'

        # === Prepare destination SVG ===
        project_svg_path = os.path.join(destination_directory, f"{page_name}.svg")

        svg = [
            '<?xml version="1.0" encoding="UTF-8" standalone="no"?>',
            f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" version="1.1" width="{page_size_px[0]}" height="{page_size_px[1]}">',
            f'  <g id="{page_name}-contents-start">',
            f'    <g id="tblock-contents-start"></g>',
            f'    <g id="tblock-contents-end"></g>',
            f'    <g id="bom" transform="{translate_bom}">',
            f'      <g id="bom-contents-start"></g>',
            f'      <g id="bom-contents-end"></g>',
            f'    </g>',
            f'    <g id="revhistory" transform="{translate_revhistory}">',
            f'      <g id="revhistory-table-contents-start"></g>',
            f'      <g id="revhistory-table-contents-end"></g>',
            f'    </g>',
            f'    <g id="buildnotes" transform="{translate_buildnotes}">',
            f'      <g id="buildnotes-table-contents-start"></g>',
            f'      <g id="buildnotes-table-contents-end"></g>',
            f'    </g>',
            f'  </g>',
            f'  <g id="{page_name}-contents-end"></g>',
            '</svg>'
        ]

        with open(project_svg_path, "w", encoding="utf-8") as f:
            f.write("\n".join(svg))

        # === Import tblock and bom SVG contents ===
        svg_utils.find_and_replace_svg_group(
            project_svg_path,
            os.path.join(destination_directory, f"{titleblock}-drawing.svg"),
            "tblock", "tblock"
        )
        if "bom" in page.get("show_items"):
            svg_utils.find_and_replace_svg_group(
                project_svg_path,
                fileio.path("bom table master svg"),
                "bom", "bom"
            )
        if "buildnotes" in page.get("show_items"):
            svg_utils.find_and_replace_svg_group(
                project_svg_path,
                fileio.path("buildnotes table svg"),
                "buildnotes-table", "buildnotes-table"
            )
        if "revhistory" in page.get("show_items"):
            svg_utils.find_and_replace_svg_group(
                project_svg_path,
                fileio.path("revhistory master svg"),
                "revhistory-table", "revhistory-table"
            )

        # === Text replacements ===
        text_map = tblock_data.get("text_replacements", {})
        with open(project_svg_path, "r", encoding="utf-8") as f:
            svg = f.read()

        for old, new in text_map.items():
            if new.startswith("pull_from_revision_history(") and new.endswith(")"):
                field_name = new[len("pull_from_revision_history("):-1]
                if field_name not in revhistory_data:
                    raise ValueError(f"[ERROR] Field '{field_name}' is missing from revision history")
                new = revhistory_data.get(field_name, "").strip()

            if "scale" in old.lower():
                new = f"{scales.get(new, 0):.3f}" if new in scales else ""

            if new == "autosheet":
                page_names = [p.get("name") for p in page_setup_contents.get("pages", [])]
                try:
                    page_num = page_names.index(page_name) + 1
                except ValueError:
                    raise ValueError(f"[ERROR] Page name '{page_name}' not found in pages list")
                total_pages = len(page_names)
                new = f"{page_num} of {total_pages}"

            if old not in svg:
                print(f"[WARN] Key '{old}' not found in titleblock SVG")

            svg = svg.replace(old, new)

        with open(project_svg_path, "w", encoding="utf-8") as f:
            f.write(svg)
            
def prep_master(page_setup_contents):
    translate = [0, -3200]
    delta_x_translate = 1600
    masters = []

    # === Discover all master SVGs in artifacts ===
    artifacts_dir = fileio.dirpath("artifacts")
    part_prefix = fileio.partnumber("pn-rev")

    for root, _, files in os.walk(artifacts_dir):
        for filename in files:
            if filename.endswith("-master.svg"):
                # Remove the "-master.svg" suffix
                base_name = filename.replace("-master.svg", "")

                # Remove partnumber prefix with optional dash
                if base_name.startswith(part_prefix + "-"):
                    master_name = base_name[len(part_prefix) + 1 :]
                elif base_name.startswith(part_prefix):
                    master_name = base_name[len(part_prefix) :]
                else:
                    master_name = base_name

                source_svg_path = os.path.join(root, filename)
                masters.append((master_name, source_svg_path))

    masters.sort(key=lambda x: x[0])  # sort alphabetically by master_name

    # === Build basic SVG contents ===
    svg = [
        '<?xml version="1.0" encoding="UTF-8" standalone="no"?>',
        '<svg xmlns="http://www.w3.org/2000/svg" version="1.1">',
        '  <g id="svg-master-contents-start">'
    ]

    for master_name, _ in masters:
        translate_str = f"translate({translate[0]},{translate[1]})"
        svg += [
            f'    <g id="{master_name}" transform="{translate_str}">',
            f'      <g id="{master_name}-contents-start"></g>',
            f'      <g id="{master_name}-contents-end"></g>',
            f'    </g>'
        ]
        translate[0] += delta_x_translate

    # Close out the SVG
    svg += [
        '  </g>',  # Close svg-master-contents-start
        '  <g id="svg-master-contents-end"></g>',
        '</svg>'
    ]

    # === Write SVG skeleton ===
    master_svg_path = path("master contents")
    with open(master_svg_path, "w", encoding="utf-8") as f:
        f.write("\n".join(svg))

    # === Replace each master group AFTER saving ===
    for master_name, source_svg_path in masters:
        svg_utils.find_and_replace_svg_group(
            master_svg_path,
            source_svg_path,
            master_name,
            master_name
        )

def update_harnice_output(page_setup_contents):
    for page_data in page_setup_contents.get("pages", []):
        page_name = page_data.get("name")
        filename = f"{fileio.partnumber('pn-rev')}-{artifact_id}-{page_name}.svg"
        filepath = os.path.join(path("page svgs"), filename)

        #pull PDF size from json in library
        titleblock_supplier = page_data.get("supplier")
        titleblock = page_data.get("titleblock", {})
        attr_library_path = os.path.join(
            path("tblock svgs"),
            page_name,
            f"{page_name}-attributes.json"
        )
        with open(attr_library_path, "r", encoding="utf-8") as f:
            tblock_attributes = json.load(f)
        page_size_in = tblock_attributes.get("page_size_in", {})
        page_size_px = [page_size_in[0] * 96, page_size_in[1] * 96]
        
        if not os.path.exists(filepath):
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(
                    #<?xml version="1.0" encoding="UTF-8" standalone="no"?>
                    f"""
        <svg xmlns="http://www.w3.org/2000/svg"
            xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape"
            version="1.1"
            width="{page_size_px[0]}"
            height="{page_size_px[1]}">
            <g id="tblock-svg-contents-start">
            </g>
            <g id="tblock-svg-contents-end"></g>
            <g id="svg-master-contents-start">
            </g>
            <g id="svg-master-contents-end"></g>
        </svg>
        """)

        #replace the master svg
        svg_utils.find_and_replace_svg_group(
            filepath, 
            path("master contents"), 
            "svg-master", 
            "svg-master"
        )

        #replace the titleblock
        svg_utils.find_and_replace_svg_group(
            filepath, 
            os.path.join(path("tblock svgs"), page_name, f"{page_name}.svg"),
            page_name, 
            "tblock-svg"
        )

def produce_multipage_pdf(page_setup_contents):
    temp_pdfs = []
    inkscape_bin = "/Applications/Inkscape.app/Contents/MacOS/inkscape"  # adjust if needed

    for page in page_setup_contents.get("pages", []):
        page_name = page.get("name")
        svg_filename = f"{fileio.partnumber("pn-rev")}-{artifact_id}-{page_name}.svg"
        svg_path = os.path.join(path("page svgs"), svg_filename)
        if not os.path.exists(svg_path):
            raise FileNotFoundError(f"[ERROR] SVG not found: {svg_path}")

        pdf_path = svg_path.replace(".svg", ".temp.pdf")

        subprocess.run([
            inkscape_bin, svg_path,
            "--export-type=pdf",
            f"--export-filename={pdf_path}"
        ], check=True)

        temp_pdfs.append(pdf_path)

    # Merge all PDFs
    subprocess.run(["pdfunite"] + temp_pdfs + [path("output pdf")], check=True)

    # Optional cleanup
    for temp in temp_pdfs:
        os.remove(temp)


page_setup_contents = update_page_setup_json()

prep_tblocks(page_setup_contents, rev_history.revision_info())

prep_master(page_setup_contents)
        #merges all building blocks into one main support_do_not_edit master svg file

update_harnice_output(page_setup_contents)
        #adds the above to the user-editable svgs in page setup, one per page

produce_multipage_pdf(page_setup_contents)