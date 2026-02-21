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
        f"{state.partnumber('pn-rev')}-{artifact_id}.tsv": "bom tsv",
        f"{state.partnumber('pn-rev')}-{artifact_id}-master.svg": "bom svg",
        "instance_data": {},
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


# ================= PROCESS INPUT INSTANCES ===========================================================
instances = fileio.read_tsv("instances list")
bom_table_contents = []
bom_instances = []
bom_tsv = []
symbols_to_build = []

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
                total_length_exact += float(instance.get("length"))
                total_length_plus_margin += float(instance.get("length")) + LENGTH_MARGIN
            else:
                total_length_exact = ""
                total_length_plus_margin = ""

    bubble_instance_name = f"bom_table_item-{i}-bubble"

    bom_table_contents.append(
        {
            "columns": {
                "bom_line_number": {
                    "instance_name": bubble_instance_name,
                    "item_type": "flagnote",
                },
                "qty": qty,
                "total_length_exact": total_length_exact,
                "mpn": mpn,
            }
        }
    )

    bom_tsv.append(
        {
            "part_of_part_number": state.partnumber("pn"),
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

    path_to_symbol = os.path.join(
        dirpath("instance_data"), "flagnote", bubble_instance_name
    )
    symbol_dict = {
        "lib_repo": "https://github.com/harnice/harnice",
        "item_type": "flagnote",
        "mpn": "bom_table_item",
        "instance_name": bubble_instance_name,
        "note_text": str(i),
    }
    library_utils.pull(
        symbol_dict,
        update_instances_list=False,
        destination_directory=path_to_symbol,
    )
    symbols_to_build.append(symbol_dict)

    # perform text replacement
    with open(
        os.path.join(path_to_symbol, f"{bubble_instance_name}-drawing.svg"), "r"
    ) as f:
        svg_content = f.read()

    svg_content = svg_content.replace("flagnote-text", str(i))

    with open(
        os.path.join(path_to_symbol, f"{bubble_instance_name}-drawing.svg"), "w"
    ) as f:
        f.write(svg_content)

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
    },
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
        },
    }
)

svg_utils.table(
    layout_dict,
    format_dict,
    columns_list,
    bom_table_contents,
    path("bom svg"),
    artifact_id,
)

# ============= WRITE CSV FILE =======================================================================
with open(
    path(
        "bom tsv",
    ),
    "w",
    newline="",
) as tsv_file:
    writer = csv.writer(tsv_file, delimiter="\t")
    writer.writerow(bom_tsv[0].keys())
    for row in bom_tsv:
        writer.writerow(row.values())

# ============= ADD SYMBOLS TO TABLE =======================================================================
for symbol in symbols_to_build:
    path_to_symbol = os.path.join(dirpath("instance_data"), symbol.get("instance_name"))
    library_utils.pull(
        symbol,
        update_instances_list=False,
        destination_directory=path_to_symbol,
    )

    # perform text replacement
    with open(
        os.path.join(path_to_symbol, f"{symbol.get('instance_name')}-drawing.svg"), "r"
    ) as f:
        svg_content = f.read()

    svg_content = svg_content.replace("flagnote-text", symbol.get("note_text"))

    with open(
        os.path.join(path_to_symbol, f"{symbol.get('instance_name')}-drawing.svg"), "w"
    ) as f:
        f.write(svg_content)

    svg_utils.find_and_replace_svg_group(
        os.path.join(path_to_symbol, f"{symbol.get('instance_name')}-drawing.svg"),
        symbol.get("instance_name"),
        path("bom svg"),
        symbol.get("instance_name"),
    )
