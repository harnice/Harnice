import os
import json
import subprocess
import shutil
from harnice import fileio, state
from harnice.utils import svg_utils, library_utils
from harnice.lists import rev_history

# ARGS
# artifact_id = "unique identifier for this instance of the macro (drawing-1)"
# scales = {"A": 1, "B": 2, "C": 3}

artifact_mpn = "pdf_generator"


def file_structure(page_name=None, page_counter=None):
    return {
        "instance_data": {
            "imported_instances": {
                "titleblock": {
                    f"{artifact_id}-{page_name}": {
                        f"{artifact_id}-{page_name}-attributes.json": "project titleblock attributes",
                        f"{artifact_id}-{page_name}-drawing.svg": "project titleblock drawing",
                    }
                },
                "macro": {
                    artifact_id: {
                        f"{state.partnumber('pn-rev')}-{artifact_id}-page_setup.json": "page setup",
                        f"{artifact_id}-mastercontents.svg": "master contents svg",
                        f"{artifact_mpn}.py": "macro script",
                        f"{state.partnumber('pn-rev')}-{artifact_id}.pdf": "output pdf",
                        "library_used_do_not_edit": {
                            "direct_from_project_titleblock": {
                                f"macro-{artifact_id}-{page_name}": {
                                    f"{artifact_id}-{page_name}-attributes.json": "macro titleblock attributes",
                                    f"{artifact_id}-{page_name}-drawing.svg": "macro titleblock drawing",
                                    f"{artifact_id}-{page_name}-drawing_with_text_replacements.svg": "tblock with text replacements",
                                }
                            }
                        },
                        "page_svgs": {
                            f"{page_counter}-{page_name}-user-editable.svg": "user editable page svg"
                        },
                    }
                },
            }
        }
    }


# ============================================
#                   MAIN FUNCTION
# ============================================
# generate file structure
fileio.silentremove(
    fileio.dirpath("direct_from_project_titleblock", structure_dict=file_structure())
)
os.makedirs(
    fileio.dirpath("direct_from_project_titleblock", structure_dict=file_structure()),
    exist_ok=True,
)
os.makedirs(fileio.dirpath("page_svgs", structure_dict=file_structure()), exist_ok=True)


# ============================================
#              PAGE SETUP JSON
# ============================================

blank_setup = {
    "pages": [
        {
            "name": "page1",
            "lib_repo": "https://github.com/harnice/harnice-library-public",
            "titleblock": "harnice_tblock-11x8.5",
            "text_replacements": {
                "tblock-key-desc": "pull_from_revision_history(desc)",
                "tblock-key-pn": "pull_from_revision_history(pn)",
                "tblock-key-drawnby": "pull_from_revision_history(drawnby)",
                "tblock-key-rev": "pull_from_revision_history(rev)",
                "tblock-key-pagedesc": "autopagedesc",
                "tblock-key-scale": "A",
                "tblock-key-sheet": "autosheet",
            },
            "show_items": [],
        }
    ]
}

page_setup_path = fileio.path("page setup", structure_dict=file_structure())

# Create or load the page setup file
if not os.path.exists(page_setup_path) or os.path.getsize(page_setup_path) == 0:
    page_data = blank_setup
else:
    try:
        with open(page_setup_path, "r", encoding="utf-8") as f:
            page_data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"[ERROR] Invalid JSON in page setup file: {page_setup_path}\n{e}"
        )

# --- STRUCTURE VALIDATION ---
if not isinstance(page_data, dict):
    raise TypeError(
        f"[ERROR] Page setup must be a dict, got {type(page_data).__name__}"
    )

if "pages" not in page_data:
    raise KeyError(f"[ERROR] Missing required key 'pages' in {page_setup_path}")

if not isinstance(page_data["pages"], list):
    raise TypeError(
        f"[ERROR] 'pages' must be a list, got {type(page_data['pages']).__name__}"
    )

for i, page in enumerate(page_data["pages"], start=1):
    if not isinstance(page, dict):
        raise TypeError(
            f"[ERROR] Page {i} in 'pages' list must be a dict, got {type(page).__name__}"
        )
    if "name" not in page:
        raise KeyError(f"[ERROR] Page {i} missing required key 'name'")
    if "titleblock" not in page:
        raise KeyError(f"[ERROR] Page {i} missing required key 'titleblock'")

# Always rewrite a clean version
with open(page_setup_path, "w", encoding="utf-8") as f:
    json.dump(page_data, f, indent=4)


# HOW TO QUERY PAGE SETUP DATA

# page_data.get('pages', [])
# → returns the list of all pages (and thier content as dict of top level list)

# page_names = [p.get("name") for p in page_data.get("pages", [])]
# → returns a list of all page names

# page_data.get('pages', [])[n]
# → returns the nth page (0-indexed) and all of its content

# page_data.get('pages', [])[n].get('name')
# → returns the 'name' of the nth page

# next(page for page in page_data.get('pages', []) if page.get('name') == "x")
# → returns the full page dictionary whose 'name' equals "x"


# ============================================
#   IMPORT TITLEBLOCKS FROM LIBRARY INTO PROJECT
# ============================================
page_names = [p.get("name") for p in page_data.get("pages", [])]
duplicates = {name for name in page_names if page_names.count(name) > 1}
if duplicates:
    raise ValueError(f"[ERROR] Duplicate page name(s) found: {', '.join(duplicates)}")

page_counter = 0
for page in page_data.get("pages", []):
    page_counter += 1
    page_name = page.get("name")
    if not page:
        raise KeyError(
            f"[ERROR] titleblock '{page_name}' not found in harnice output contents"
        )

    # === Pull from library ===
    library_utils.pull(
        {
            "instance_name": f"{artifact_id}-{page_name}",
            "mpn": page.get("titleblock"),
            "lib_repo": page.get("lib_repo"),
            "item_type": "titleblock",
        },
        update_instances_list=False,
    )

    # ============================================
    #     COPY TITLEBLOCKS TO MACRO DIRECTORY
    # ============================================

    # === Copy from imported instances to this macro's library_used_do_not_edit directory ===
    os.makedirs(
        fileio.dirpath(
            f"macro-{artifact_id}-{page_name}",
            structure_dict=file_structure(page_name=page_name),
        ),
        exist_ok=True,
    )
    shutil.copy(
        fileio.path(
            "project titleblock attributes",
            structure_dict=file_structure(page_name=page_name),
        ),
        fileio.path(
            "macro titleblock attributes",
            structure_dict=file_structure(page_name=page_name),
        ),
    )
    shutil.copy(
        fileio.path(
            "project titleblock drawing",
            structure_dict=file_structure(page_name=page_name),
        ),
        fileio.path(
            "macro titleblock drawing",
            structure_dict=file_structure(page_name=page_name),
        ),
    )

    # ============================================
    #        PREP TEXT REPLACEMENTS SVG
    # ============================================
    with open(
        fileio.path(
            "macro titleblock attributes",
            structure_dict=file_structure(page_name=page_name),
        ),
        "r",
        encoding="utf-8",
    ) as f:
        tblock_attributes = json.load(f)

    # === Page size in pixels ===
    page_size_in = tblock_attributes.get("page_size_in", [11, 8.5])
    page_size_px = [int(page_size_in[0] * 96), int(page_size_in[1] * 96)]

    # === Prepare text replacements SVG ===
    svg = [
        '<?xml version="1.0" encoding="UTF-8" standalone="no"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" version="1.1" width="{page_size_px[0]}" height="{page_size_px[1]}">',
        f'  <g id="{page_counter}-{page_name}-contents-start">',
        f'    <g id="tblock-contents-start"></g>',
        f'    <g id="tblock-contents-end"></g>',
        f"  </g>",
        f'  <g id="{page_counter}-{page_name}-contents-end"></g>',
        "</svg>",
    ]

    with open(
        fileio.path(
            "tblock with text replacements",
            structure_dict=file_structure(
                page_counter=page_counter, page_name=page_name
            ),
        ),
        "w",
        encoding="utf-8",
    ) as f:
        f.write("\n".join(svg))

    # === Import tblock and bom SVG contents ===
    svg_utils.find_and_replace_svg_group(
        fileio.path(
            "tblock with text replacements",
            structure_dict=file_structure(
                page_counter=page_counter, page_name=page_name
            ),
        ),
        fileio.path(
            "macro titleblock drawing",
            structure_dict=file_structure(
                page_counter=page_counter, page_name=page_name
            ),
        ),
        "tblock",
        "tblock",
    )

    # === Text replacements ===
    text_map = page.get("text_replacements", {})
    with open(
        fileio.path(
            "tblock with text replacements",
            structure_dict=file_structure(
                page_counter=page_counter, page_name=page_name
            ),
        ),
        "r",
        encoding="utf-8",
    ) as f:
        svg = f.read()

    for old, new in text_map.items():
        if new.startswith("pull_from_revision_history(") and new.endswith(")"):
            field_name = new[len("pull_from_revision_history(") : -1]
            if field_name not in rev_history.info():
                raise ValueError(
                    f"[ERROR] Field '{field_name}' is missing from revision history"
                )
            new = rev_history.info().get(field_name, "").strip()

        if "scale" in old.lower():
            new = f"{scales.get(new, 0):.3f}" if new in scales else ""

        if new == "autosheet":
            page_names = [p.get("name") for p in page_data.get("pages", [])]
            total_pages = len(page_names)
            new = f"{page_counter} of {total_pages}"

        if new == "autopagedesc":
            page_names = [p.get("name") for p in page_data.get("pages", [])]
            total_pages = len(page_names)
            new = page_name

        if old not in svg:
            print(f"[WARN] Key '{old}' not found in titleblock SVG")

        svg = svg.replace(old, new)

    with open(
        fileio.path(
            "tblock with text replacements",
            structure_dict=file_structure(
                page_counter=page_counter, page_name=page_name
            ),
        ),
        "w",
        encoding="utf-8",
    ) as f:
        f.write(svg)


# ============================================
#            PREP MASTER SVG
# searches imported_instances for anything that ends in -master.svg and adds it to this file
# ============================================
translate = [0, -3200]
delta_x_translate = 0
masters = []

# Discover all master SVGs in macros folder
part_prefix = state.partnumber("pn-rev")

for root, _, files in os.walk(fileio.dirpath("imported_instances")):
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

# write the svg structure
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

svg += [
    "  </g>",  # Close svg-master-contents-start
    '  <g id="svg-master-contents-end"></g>',
    "</svg>",
]

master_svg_path = fileio.path("master contents svg", structure_dict=file_structure())
with open(master_svg_path, "w", encoding="utf-8") as f:
    f.write("\n".join(svg))

# fetch content from each -master.svg into the master contents svg
for master_name, source_svg_path in masters:
    svg_utils.find_and_replace_svg_group(
        master_svg_path, source_svg_path, master_name, master_name
    )


# ============================================
#         PREPARE USER EDITABLE PAGE SVGS
# these are the ones the user should edit to place their content
# ============================================
page_counter = 0
for page in page_data.get("pages", []):
    page_name = page.get("name")
    page_counter += 1

    # pull PDF size from json in library
    with open(
        fileio.path(
            "macro titleblock attributes",
            structure_dict=file_structure(page_name=page_name),
        ),
        "r",
        encoding="utf-8",
    ) as f:
        tblock_attributes = json.load(f)
    page_size_in = tblock_attributes.get("page_size_in", {})
    page_size_px = [page_size_in[0] * 96, page_size_in[1] * 96]

    if not os.path.exists(
        fileio.path(
            "user editable page svg",
            structure_dict=file_structure(
                page_counter=page_counter, page_name=page_name
            ),
        )
    ):
        with open(
            fileio.path(
                "user editable page svg",
                structure_dict=file_structure(
                    page_counter=page_counter, page_name=page_name
                ),
            ),
            "w",
            encoding="utf-8",
        ) as f:
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
        fileio.path(
            "user editable page svg",
            structure_dict=file_structure(
                page_counter=page_counter, page_name=page_name
            ),
        ),
        fileio.path("master contents svg", structure_dict=file_structure()),
        "svg-master",
        "svg-master",
    )

    # replace the titleblock
    svg_utils.find_and_replace_svg_group(
        fileio.path(
            "user editable page svg",
            structure_dict=file_structure(
                page_counter=page_counter, page_name=page_name
            ),
        ),
        fileio.path(
            "tblock with text replacements",
            structure_dict=file_structure(
                page_counter=page_counter, page_name=page_name
            ),
        ),
        f"{page_counter}-{page_name}",
        "tblock-svg",
    )

# ============================================
#            PRODUCE MULTIPAGE PDF
# ============================================
temp_pdfs = []
inkscape_bin = "/Applications/Inkscape.app/Contents/MacOS/inkscape"  # adjust if needed

page_counter = 0
for page_name in [p.get("name") for p in page_data.get("pages", [])]:
    page_counter += 1
    svg_path = fileio.path(
        "user editable page svg",
        structure_dict=file_structure(page_counter=page_counter, page_name=page_name),
    )
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
subprocess.run(
    ["pdfunite"]
    + temp_pdfs
    + [fileio.path("output pdf", structure_dict=file_structure())],
    check=True,
)

# Optional cleanup
for temp in temp_pdfs:
    os.remove(temp)
