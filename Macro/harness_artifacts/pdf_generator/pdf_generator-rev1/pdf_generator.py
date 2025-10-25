import os
import json
import subprocess
import shutil
from harnice import fileio
from harnice.utils import svg_utils, library_utils
from harnice.lists import rev_history

artifact_mpn = "pdf_generator"

def file_structure(page_name=None, page_counter=None):
    return {
        "imported_instances":{
            "Titleblock":{
                f"{artifact_id}-{page_name}":{
                    f"{artifact_id}-{page_name}-attributes.json": "project titleblock attributes",
                    f"{artifact_id}-{page_name}-drawing.svg": "project titleblock drawing"
                }
            },
            "Macro":{
                artifact_id:{
                    f"{fileio.partnumber("pn-rev")}-{artifact_id}-page_setup.json": "page setup",
                    f"{artifact_id}-mastercontents.svg": "master contents svg",
                    f"{artifact_mpn}.py": "macro script",
                    f"{fileio.partnumber("pn-rev")}-{artifact_id}.pdf": "output pdf",
                    "library_used_do_not_edit":{
                        "Titleblocks":{
                            f"{artifact_id}-{page_name}":{
                                f"{artifact_id}-{page_name}-attributes.json": "macro titleblock attributes",
                                f"{artifact_id}-{page_name}-drawing.svg": "macro titleblock drawing"
                            }
                        },
                    },
                    "page_svgs":{
                        f"{page_counter}-{page_name}-drawing.svg": "page svg"
                    }
                }
            }
        }
    }

def generate_file_structure():
    os.makedirs(fileio.dirpath("imported instances", structure_dict=file_structure()), exist_ok=True)
    os.makedirs(fileio.dirpath("Macro", structure_dict=file_structure()), exist_ok=True)
    fileio.silentremove(fileio.dirpath(artifact_id, structure_dict=file_structure()))
    os.makedirs(fileio.dirpath("library_used_do_not_edit", structure_dict=file_structure()), exist_ok=True)
    os.makedirs(fileio.dirpath("Titleblocks", structure_dict=file_structure()), exist_ok=True)


def update_page_setup_json():
    """Ensure page setup JSON exists and return its contents."""

    # Default Titleblock Setup
    blank_setup = {
        "pages": [
            {
                "name": "page1",
                "lib_repo": "https://github.com/kenyonshutt/harnice-library-public",
                "titleblock": "harnice_tblock-11x8.5",
                "text_replacements": {
                    "tblock-key-desc": "pull_from_revision_history(desc)",
                    "tblock-key-pn": "pull_from_revision_history(pn)",
                    "tblock-key-drawnby": "pull_from_revision_history(drawnby)",
                    "tblock-key-rev": "pull_from_revision_history(rev)",
                    "tblock-key-releaseticket": "",
                    "tblock-key-scale": "A",
                    "tblock-key-sheet": "autosheet",
                },
                "show_items": [],  # "bom", "buildnotes", "revhistory"
            }
        ]
    }

    # Create or load the page setup file
    if (
        not os.path.exists(fileio.path("page setup", structure_dict=file_structure()))
        or os.path.getsize(fileio.path("page setup", structure_dict=file_structure())) == 0
    ):
        page_data = blank_setup
    else:
        try:
            with open(fileio.path("page setup", structure_dict=file_structure()), "r", encoding="utf-8") as f:
                page_data = json.load(f)
        except json.JSONDecodeError:
            page_data = blank_setup

    # Always write back a valid version
    TODO: FIGURE OUT WHY THIS IS NOT DUMPING JSON
    print(f"!!!!!!!!!!Page setup path: {fileio.path('page setup', structure_dict=file_structure())}")
    with open(fileio.path("page setup", structure_dict=file_structure()), "w", encoding="utf-8") as f:
        json.dump(page_data, f, indent=4)

    return page_data


def prep_tblocks(page_setup_contents, revhistory_data):
    # === Validate page name uniqueness ===
    page_names = [p.get("name") for p in page_setup_contents.get("pages", [])]
    duplicates = {name for name in page_names if page_names.count(name) > 1}
    if duplicates:
        raise ValueError(
            f"[ERROR] Duplicate page name(s) found: {', '.join(duplicates)}"
        )

    page_counter = 0
    for page in page_setup_contents.get("pages", []):
        page_counter += 1
        page_name = page.get("name")
        if not page:
            raise KeyError(
                f"[ERROR] Titleblock '{page_name}' not found in harnice output contents"
            )

        titleblock = page.get("titleblock")

        # === Pull from library ===
        library_utils.pull(
            {
                "instance_name": f"{artifact_id}-{page_name}",
                "mpn": page.get("titleblock"),
                "lib_repo": page.get("lib_repo"),
                "item_type": "Titleblock",
            }, update_instances_list=False
        )

        # === Copy from imported instances to this macro's library_used_do_not_edit directory ===
        #TODO: #486

        with open(fileio.path("titleblock attributes", structure_dict=file_structure(page_name)), "r", encoding="utf-8") as f:
            tblock_attributes = json.load(f)

        # === Page size in pixels ===
        page_size_in = tblock_attributes.get("page_size_in", [11, 8.5])
        page_size_px = [int(page_size_in[0] * 96), int(page_size_in[1] * 96)]

        # === Prepare destination SVG ===
        svg = [
            '<?xml version="1.0" encoding="UTF-8" standalone="no"?>',
            f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" version="1.1" width="{page_size_px[0]}" height="{page_size_px[1]}">',
            f'  <g id="{page_name}-contents-start">',
            f'    <g id="tblock-contents-start"></g>',
            f'    <g id="tblock-contents-end"></g>',
            f"  </g>",
            f'  <g id="{page_name}-contents-end"></g>',
            "</svg>",
        ]

        with open(svg_build_path, "w", encoding="utf-8") as f:
            f.write("\n".join(svg))

        # === Import tblock and bom SVG contents ===
        svg_utils.find_and_replace_svg_group(
            svg_build_path,
            svg_destination_path,
            "tblock",
            "tblock",
        )

        # === Text replacements ===
        text_map = tblock_data.get("text_replacements", {})
        with open(project_svg_path, "r", encoding="utf-8") as f:
            svg = f.read()

        for old, new in text_map.items():
            if new.startswith("pull_from_revision_history(") and new.endswith(")"):
                field_name = new[len("pull_from_revision_history(") : -1]
                if field_name not in revhistory_data:
                    raise ValueError(
                        f"[ERROR] Field '{field_name}' is missing from revision history"
                    )
                new = revhistory_data.get(field_name, "").strip()

            if "scale" in old.lower():
                new = f"{scales.get(new, 0):.3f}" if new in scales else ""

            if new == "autosheet":
                page_names = [
                    p.get("name") for p in page_setup_contents.get("pages", [])
                ]
                total_pages = len(page_names)
                new = f"{page_counter} of {total_pages}"

            if old not in svg:
                print(f"[WARN] Key '{old}' not found in titleblock SVG")

            svg = svg.replace(old, new)

        with open(project_svg_path, "w", encoding="utf-8") as f:
            f.write(svg)


def prep_master(page_setup_contents):
    translate = [0, -3200]
    delta_x_translate = 0
    masters = []

    # === Discover all master SVGs in macros folder ===
    macros_dir = fileio.dirpath("macros")
    part_prefix = fileio.partnumber("pn-rev")

    for root, _, files in os.walk(macros_dir):
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
        '  <g id="svg-master-contents-start">',
    ]

    for master_name, _ in masters:
        translate_str = f"translate({translate[0]},{translate[1]})"
        svg += [
            f'    <g id="{master_name}" transform="{translate_str}">',
            f'      <g id="{master_name}-contents-start"></g>',
            f'      <g id="{master_name}-contents-end"></g>',
            f"    </g>",
        ]
        translate[0] += delta_x_translate

    # Close out the SVG
    svg += [
        "  </g>",  # Close svg-master-contents-start
        '  <g id="svg-master-contents-end"></g>',
        "</svg>",
    ]

    # === Write SVG skeleton ===
    master_svg_path = path("master contents")
    with open(master_svg_path, "w", encoding="utf-8") as f:
        f.write("\n".join(svg))

    # === Replace each master group AFTER saving ===
    for master_name, source_svg_path in masters:
        svg_utils.find_and_replace_svg_group(
            master_svg_path, source_svg_path, master_name, master_name
        )


def update_harnice_output(page_setup_contents):
    for page_data in page_setup_contents.get("pages", []):
        page_name = page_data.get("name")
        filename = f"{fileio.partnumber('pn-rev')}-{artifact_id}-{page_name}.svg"
        filepath = os.path.join(path("page svgs"), filename)

        # pull PDF size from json in library
        titleblock_lib_repo = page_data.get("lib_repo")
        titleblock = page_data.get("titleblock", {})
        attr_library_path = os.path.join(
            path("tblock svgs"), page_name, f"{page_name}-attributes.json"
        )
        with open(attr_library_path, "r", encoding="utf-8") as f:
            tblock_attributes = json.load(f)
        page_size_in = tblock_attributes.get("page_size_in", {})
        page_size_px = [page_size_in[0] * 96, page_size_in[1] * 96]

        if not os.path.exists(filepath):
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(
                    # <?xml version="1.0" encoding="UTF-8" standalone="no"?>
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
        """
                )

        # replace the master svg
        svg_utils.find_and_replace_svg_group(
            filepath, path("master contents"), "svg-master", "svg-master"
        )

        # replace the titleblock
        svg_utils.find_and_replace_svg_group(
            filepath,
            os.path.join(path("tblock svgs"), page_name, f"{page_name}.svg"),
            page_name,
            "tblock-svg",
        )


def produce_multipage_pdf(page_setup_contents):
    temp_pdfs = []
    inkscape_bin = (
        "/Applications/Inkscape.app/Contents/MacOS/inkscape"  # adjust if needed
    )

    for page in page_setup_contents.get("pages", []):
        page_name = page.get("name")
        svg_filename = f"{fileio.partnumber('pn-rev')}-{artifact_id}-{page_name}.svg"
        svg_path = os.path.join(path("page svgs"), svg_filename)
        if not os.path.exists(svg_path):
            raise FileNotFoundError(f"[ERROR] SVG not found: {svg_path}")

        pdf_path = svg_path.replace(".svg", ".temp.pdf")

        subprocess.run(
            [
                inkscape_bin,
                svg_path,
                "--export-type=pdf",
                f"--export-filename={pdf_path}",
            ],
            check=True,
        )

        temp_pdfs.append(pdf_path)

    # Merge all PDFs
    subprocess.run(["pdfunite"] + temp_pdfs + [path("output pdf")], check=True)

    # Optional cleanup
    for temp in temp_pdfs:
        os.remove(temp)


page_setup_contents = update_page_setup_json()

prep_tblocks(page_setup_contents, rev_history.info())

prep_master(page_setup_contents)
# merges all building blocks into one main support_do_not_edit master svg file

update_harnice_output(page_setup_contents)
# adds the above to the user-editable svgs in page setup, one per page

produce_multipage_pdf(page_setup_contents)
