from modulefinder import test
import os
import csv
from harnice import fileio, state
from harnice.utils import svg_utils, library_utils

artifact_mpn = "cutlist_exporter_bottom_up"

# ============== SETUP VARIABLES ===============================================
LENGTH_MARGIN = 12


# =============== PATHS ===================================================================================
def macro_file_structure():
    return {
        f"{state.partnumber('pn-rev')}-{artifact_id}.tsv": "cutlist tsv",
        f"{state.partnumber('pn-rev')}-{artifact_id}-master.svg": "cutlist svg",
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
cutlist_table_contents = []
cutlist_instances = []
cutlist_tsv = []
symbols_to_build = []

highest_bom_number = 0
for instance in instances:
    if instance.get("bom_line_number") not in ["", None]:
        if instance.get("length") not in ["", None]:
            cutlist_instances.append(instance)
        if int(instance.get("bom_line_number")) > highest_bom_number:
            highest_bom_number = int(instance.get("bom_line_number"))

for i in range(1, highest_bom_number + 1):
    qty = 0
    by_length_item = False
    cuts_of_this_bom_item = []
    total_length_exact = 0
    total_length_plus_margin = 0
    mpn = ""
    item_type = ""
    lib_repo = ""
    lib_subpath = ""

    for instance in cutlist_instances:
        if int(instance.get("bom_line_number")) == i:
            by_length_item = True
            qty += 1
            mpn = instance.get("mpn")
            item_type = instance.get("item_type")
            lib_repo = instance.get("lib_repo")
            lib_subpath = instance.get("lib_subpath")
            total_length_exact += float(instance.get("length"))
            total_length_plus_margin += float(instance.get("length")) + LENGTH_MARGIN

            cuts_of_this_bom_item.append({
                "name": instance.get("instance_name"),
                "length": float(instance.get("length")),
                "length_plus_margin": float(instance.get("length")) + LENGTH_MARGIN

            })

    if by_length_item:
        bubble_instance_name = f"cutlist_table_item-{i}-bubble"

        cutlist_table_contents.append(
            {
                "columns": {
                    "bom_line_number": {
                        "instance_name": bubble_instance_name,
                        "item_type": "flagnote",
                    },
                    "name": mpn,
                    "length": total_length_exact,
                    "length_plus_margin": total_length_plus_margin,
                },
                "format_key": "total_line"
            }
        )

        for cut in cuts_of_this_bom_item:

            arrow_instance_name = f"cutlist_table_item-{cut.get("name")}-arrow"

            cutlist_table_contents.append(
                {
                    "columns": {
                        "bom_line_number": {
                            "instance_name": arrow_instance_name,
                            "item_type": "flagnote",
                        },
                        "name": cut.get("name"),
                        "length": cut.get("length"),
                        "length_plus_margin": cut.get("length_plus_margin")
                    }
                }
            )


            cutlist_tsv.append(
                {
                    "part_of_part_number": state.partnumber("pn"),
                    "bom_line_number": i,
                    "mpn": mpn,
                    "instance_name": cut.get("name"),
                    "lib_repo": lib_repo,
                    "lib_subpath": lib_subpath,
                    "cut_length_exact": cut.get("length"),
                    "length_plus_margin": cut.get("length_plus_margin"),
                }
            )

            # make the symbol for each cut

            path_to_symbol = os.path.join(
                dirpath("instance_data"), "flagnote", arrow_instance_name
            )
            symbol_dict = {
                "lib_repo": "https://github.com/harnice/harnice",
                "item_type": "flagnote",
                "mpn": "down_right_arrow",
                "instance_name": arrow_instance_name
            }
            library_utils.pull(
                symbol_dict,
                update_instances_list=False,
                destination_directory=path_to_symbol,
            )
            symbols_to_build.append(symbol_dict)

        # make the symbol for the bom total line

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
    "total_line": {
        "font_weight": "B"
    }
}

columns_list = [
    {
        "name": "bom_line_number",
        "width": 0.375 * 96,
    },
    {
        "name": "name",
        "width": 2 * 96,
        "justify": "left",
    },
    {
        "name": "length",
        "width": 0.75 * 96,
    },
    {
        "name": "length_plus_margin",
        "width": 0.75 * 96,
    },
]
# append header row at the end because we want it on the bottom of the table
cutlist_table_contents.append(
    {
        "format_key": "header",
        "columns": {
            "bom_line_number": "ITEM",
            "length": "LENGTH (in)",
            "length_plus_margin": "L + MARGIN",
        },
    }
)

svg_utils.table(
    layout_dict,
    format_dict,
    columns_list,
    cutlist_table_contents,
    path("cutlist svg"),
    artifact_id,
)

# ============= WRITE CSV FILE =======================================================================
with open(
    path(
        "cutlist tsv",
    ),
    "w",
    newline="",
) as tsv_file:
    writer = csv.writer(tsv_file, delimiter="\t")
    writer.writerow(cutlist_tsv[0].keys())
    for row in cutlist_tsv:
        writer.writerow(row.values())

# ============= ADD SYMBOLS TO TABLE =======================================================================
for symbol in symbols_to_build:
    path_to_symbol = os.path.join(dirpath("instance_data"), "flagnote", symbol.get("instance_name"))

    svg_utils.find_and_replace_svg_group(
        os.path.join(path_to_symbol, f"{symbol.get('instance_name')}-drawing.svg"),
        symbol.get("instance_name"),
        path("cutlist svg"),
        symbol.get("instance_name"),
    )
