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


# =============== PATHS ===================================================================================
def macro_file_structure(page_name=None, page_counter=None):
    return {
        f"{state.partnumber('pn-rev')}-{artifact_id}-page_setup.json": "page setup",
        f"{artifact_id}-mastercontents.svg": "master contents svg",
        f"{state.partnumber('pn-rev')}-{artifact_id}.pdf": "output pdf",
        "page_svgs": {
            f"{page_counter}-{page_name}-user-editable.svg": "user editable page svg"
        },
    }


if base_directory is None:  # path between cwd and the file structure for this macro
    base_directory = os.path.join("instance_data", "macro", artifact_id)


def path(target_value, page_name=None, page_counter=None):
    return fileio.path(
        target_value,
        structure_dict=macro_file_structure(page_name, page_counter),
        base_directory=base_directory,
    )


def dirpath(target_value, page_name=None, page_counter=None):
    # target_value = None will return the root of this macro
    return fileio.dirpath(
        target_value,
        structure_dict=macro_file_structure(page_name, page_counter),
        base_directory=base_directory,
    )


os.makedirs(
    dirpath("page_svgs"),
    exist_ok=True,
)
# ==========================================================================================================


# ==========================================================================================================
#              PAGE SETUP JSON
# ==========================================================================================================

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

page_setup_path = path("page setup")

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

page_names = [p.get("name") for p in page_data.get("pages", [])]
duplicates = {name for name in page_names if page_names.count(name) > 1}
if duplicates:
    raise ValueError(f"[ERROR] Duplicate page name(s) found: {', '.join(duplicates)}")

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

# ==========================================================================================================
#            PREP MASTER SVG
# searches imported_instances for anything that ends in -master.svg and adds it to this file
# ==========================================================================================================
masters_translate = [0, -3200]
masters = []

# Discover all master SVGs in a folder of the entire project (output of the other macros)
part_prefix = state.partnumber("pn-rev")
directory_to_search = os.path.join(
    fileio.dirpath(None),
    "instance_data",
)

for root, _, files in os.walk(directory_to_search):
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
    translate_str = f"translate({masters_translate[0]},{masters_translate[1]})"
    svg += [
        f'    <g id="{master_name}" transform="{translate_str}">',
        f'      <g id="{master_name}-contents-start"></g>',
        f'      <g id="{master_name}-contents-end"></g>',
        f"    </g>",
    ]

svg += [
    "  </g>",  # Close svg-master-contents-start
    '  <g id="svg-master-contents-end"></g>',
    "</svg>",
]

with open(path("master contents svg"), "w", encoding="utf-8") as f:
    f.write("\n".join(svg))

# fetch content from each -master.svg into the master contents svg
for master_name, source_svg_path in masters:
    svg_utils.find_and_replace_svg_group(
        source_svg_path, master_name, path("master contents svg"), master_name
    )

# ==========================================================================================================
#             PREP USER EDITABLE PAGE SVGS
# ==========================================================================================================
page_counter = 0
for page in page_data.get("pages", []):
    page_counter += 1
    page_name = page.get("name")

    # if you want to import one or more pages into different locations, do that here
    # to import into the project root:
    #     titleblock_location = os.path.join(fileio.dirpath(None), "instance_data", "titleblock", f"{artifact_id}-{page_name}")
    # to import into this macro:
    lib_imported_dirpath = os.path.join(
        dirpath(None), "instance_data", "titleblock", f"{artifact_id}-{page_name}"
    )

    # if you're manually editing the titleblock before it gets imported, remove this line, though replacements won't work
    fileio.silentremove(lib_imported_dirpath)

    lib_imported_drawing_filepath = os.path.join(
        lib_imported_dirpath, f"{artifact_id}-{page_name}-drawing.svg"
    )
    lib_imported_attributes_filepath = os.path.join(
        lib_imported_dirpath, f"{artifact_id}-{page_name}-attributes.json"
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
        destination_directory=lib_imported_dirpath,
    )

    # === Perform text replacements in imported titleblock ===
    text_map = page.get("text_replacements", {})
    with open(
        lib_imported_drawing_filepath,
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

        svg = svg.replace(old, new)

    with open(lib_imported_drawing_filepath, "w", encoding="utf-8") as f:
        f.write(svg)

    # === Make user editable page if doesn't exist ===
    with open(lib_imported_attributes_filepath) as f:
        tblock_attributes = json.load(f)

    # === Page size in pixels ===
    page_size_in = tblock_attributes.get("page_size_in")
    page_size_px = [int(page_size_in[0] * 96), int(page_size_in[1] * 96)]

    if not os.path.exists(
        path("user editable page svg", page_name=page_name, page_counter=page_counter)
    ):
        with open(
            path(
                "user editable page svg", page_name=page_name, page_counter=page_counter
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
                    <g id="tblock-contents-start">
                    </g>
                    <g id="tblock-contents-end"></g>
                    <g id="svg-master-contents-start">
                    </g>
                    <g id="svg-master-contents-end"></g>
                </svg>
                """
            )

    # === replace tblock contents ===
    svg_utils.find_and_replace_svg_group(
        lib_imported_drawing_filepath,
        "tblock",
        path("user editable page svg", page_name=page_name, page_counter=page_counter),
        "tblock",
    )

    # replace the master svg
    svg_utils.find_and_replace_svg_group(
        path("master contents svg"),
        "svg-master",
        path("user editable page svg", page_name=page_name, page_counter=page_counter),
        "svg-master",
    )

# ============================================
#            PRODUCE MULTIPAGE PDF
# ============================================
temp_pdfs = []
inkscape_bin = "/Applications/Inkscape.app/Contents/MacOS/inkscape"  # adjust if needed

page_counter = 0
for page_name in [p.get("name") for p in page_data.get("pages", [])]:
    page_counter += 1
    svg_path = path(
        "user editable page svg", page_name=page_name, page_counter=page_counter
    )
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
    ["pdfunite"] + temp_pdfs + [path("output pdf")],
    check=True,
)

# Optional cleanup
for temp in temp_pdfs:
    os.remove(temp)
