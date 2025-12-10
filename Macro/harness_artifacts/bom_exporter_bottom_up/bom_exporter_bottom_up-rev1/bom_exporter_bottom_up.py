import os
import csv
from harnice import fileio, state
from harnice.utils import svg_utils, library_utils

artifact_mpn = "bom_exporter_bottom_up"

# ============== SETUP VARIABLES ===============================================
LENGTH_MARGIN = 12


# =============== PATHS ===================================================================================
def macro_file_structure():
    return {
        f"{state.partnumber('pn-rev')}-{artifact_id}-bom.tsv": "bom tsv",
        f"{state.partnumber('pn-rev')}-{artifact_id}-bom-master.svg": "bom svg",
    }


if base_directory is None:  # path between cwd and the file structure for this macro
    base_directory = os.path.join("instance_data", "macro", artifact_id)


def path(target_value):
    return fileio.path(
        target_value,
        structure_dict=macro_file_structure(),
        base_directory=base_directory,
    )


def dirpath(target_value):
    # target_value = None will return the root of this macro
    return fileio.dirpath(
        target_value,
        structure_dict=macro_file_structure(),
        base_directory=base_directory,
    )

bom_table_contents = []

# ================= PROCESS INPUT INSTANCES ===========================================================
instances = fileio.read_tsv("instances list")
bom_instances = []
bom_tsv = []

highest_bom_number = 0
for instance in instances:
    if instance.get("bom_line_number") not in ["", None]:
        bom_instances.append(instance)
        if int(instance.get("bom_line_number")) > highest_bom_number:
            highest_bom_number = int(instance.get("bom_line_number"))

for i in range(1, highest_bom_number + 1):
    qty = 0
    total_length_exact = 0
    total_length_plus_margin = 0
    mpn = ""
    item_type = ""
    lib_repo = ""
    lib_subpath = ""

    for instance in bom_instances:
        if int(instance.get("bom_line_number")) == i:
            qty += 1
            mpn = instance.get("mpn")
            item_type = instance.get("item_type")
            lib_repo = instance.get("lib_repo")
            lib_subpath = instance.get("lib_subpath")
            if not instance.get("length") == "":
                total_length_exact += int(instance.get("length"))
                total_length_plus_margin += (
                    int(instance.get("length")) + LENGTH_MARGIN
                )
            else:
                total_length_exact = ""
                total_length_plus_margin = ""

    bom_table_contents.append(
        {
            "columns": {
                "bom_line_number": i,
                "qty": qty,
                "total_length_exact": total_length_exact,
                "mpn": mpn,
            }
        }
    )

    bom_tsv.append(
        {
            "bom_line_number": i,
            "mpn": mpn,
            "item_type": item_type,
            "qty": qty,
            "lib_repo": lib_repo,
            "lib_subpath": lib_subpath,
            "total_length_exact": total_length_exact,
            "total_length_plus_margin": total_length_plus_margin,
        }
    )

# ============= BUILD TABLE ===========================================================
layout_dict = {
    "origin_corner": "bottom-right",
    "build_direction": "up",
}

format_dict = {
    "globals": {
        "font_size": 8,
        "font_family": "Arial, Helvetica, sans-serif",
    },
    "header": {
        "font_weight": "B",
        "fill_color": "lightgray",
    }
}

columns_list = [
    {
        "name": "bom_line_number",
        "width": 0.375 * 96,
    },
    {
        "name": "qty",
        "width": 0.375 * 96,
    },
    {
        "name": "total_length_exact",
        "width": 0.75 * 96,
    },
    {
        "name": "mpn",
        "width": 1.75 * 96,
        "justify": "left",
    },
]
# append header row at the end because we want it on the bottom of the table
bom_table_contents.append(
    {
        "format_key": "header",
        "columns": {
            "bom_line_number": "ITEM",
            "qty": "QTY",
            "total_length_exact": "LENGTH (in)",
            "mpn": "MPN",
        }
    }
)

svg_utils.table(
    layout_dict,
    format_dict,
    columns_list,
    bom_table_contents,
    fileio.dirpath(None, base_directory=base_directory),
    artifact_id
)

# ============= WRITE CSV FILE =======================================================================
with open(path("bom tsv", ), "w", newline="") as tsv_file:
    writer = csv.writer(tsv_file, delimiter="\t")
    writer.writerow(bom_tsv[0].keys())
    for row in bom_tsv:
        writer.writerow(row.values())

# ============= ADD SYMBOLS TO TABLE =======================================================================

"""
for symbol in symbols_to_build:
    path_to_symbol = os.path.join(dirpath("instance_data"), symbol.get("instance_name"))
    library_utils.pull(
        symbol,
        update_instances_list=False,
        destination_directory=path_to_symbol,
    )

    # perform text replacement
    with open(os.path.join(path_to_symbol, f"{symbol.get('instance_name')}-drawing.svg"), "r") as f:
        svg_content = f.read()

    svg_content = svg_content.replace("flagnote-text", symbol.get("note_text"))

    with open(os.path.join(path_to_symbol, f"{symbol.get('instance_name')}-drawing.svg"), "w") as f:
        f.write(svg_content)

    svg_utils.find_and_replace_svg_group(
        os.path.join(path_to_symbol, f"{symbol.get('instance_name')}-drawing.svg"),
        symbol.get("instance_name"),
        path("build notes table svg"),
        symbol.get("instance_name")
    )
"""