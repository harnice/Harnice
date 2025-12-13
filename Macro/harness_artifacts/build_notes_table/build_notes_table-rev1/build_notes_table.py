import os
from harnice import fileio, state
from harnice.utils import svg_utils, library_utils

artifact_mpn = "build_notes_table"


# =============== PATHS ===================================================================================
def macro_file_structure(identifier=None):
    return {
        f"{state.partnumber('pn-rev')}-{artifact_id}-master.svg": "build notes table svg",
        f"{state.partnumber('pn-rev')}-{artifact_id}-build_notes-list.tsv": "build_notes list",
        "instance_data": {},
    }


if base_directory is None:  # path between cwd and the file structure for this macro
    base_directory = os.path.join("instance_data", "macro", artifact_id)


def path(target_value, identifier=None):
    return fileio.path(
        target_value,
        structure_dict=macro_file_structure(identifier),
        base_directory=base_directory,
    )


def dirpath(target_value, identifier=None):
    # target_value = None will return the root of this macro
    return fileio.dirpath(
        target_value,
        structure_dict=macro_file_structure(identifier),
        base_directory=base_directory,
    )


# ================= INITIALIZE TABLE =========================================================================================

layout_dict = {
    "origin_corner": "top-left",
    "build_direction": "down",
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
    "row_with_bubble": {
        "row_height": 0.4 * 96,
    },
}

columns_list = [
    {
        "name": "build_note_number",
        "width": 0.5 * 96,
    },
    {
        "name": "note",
        "width": 3.375 * 96,
        "justify": "left",
    },
]

content_list = []

# ============= WRITE HEADER ROW =======================================================================
content_list.append(
    {
        "format_key": "header",
        "columns": {
            "note": "BUILD NOTES",
        },
    }
)
# ============= PROCESS INPUT INSTANCES =======================================================================
symbols_to_build = []

for instance in input_instances:
    build_note_number = instance.get("note_number")
    number_column = build_note_number
    note_column = instance.get("note_text")
    has_shape = False

    # Pull bubble from the library if there is a shape
    if not instance.get("note_affected_instances") == "[]":
        number_column = {
            "lib_repo": instance.get("lib_repo"),
            "item_type": "flagnote",
            "mpn": instance.get("mpn"),
            "instance_name": f"bubble{build_note_number}",
            "note_text": build_note_number,
        }
        content_list.append(
            {
                "format_key": "row_with_bubble",
                "columns": {
                    "build_note_number": number_column,
                    "note": note_column,
                },
            }
        )
        symbols_to_build.append(number_column)

    else:
        content_list.append(
            {
                "columns": {
                    "build_note_number": number_column,
                    "note": note_column,
                }
            }
        )

# ============= BUILD TABLE =======================================================================

svg_utils.table(
    layout_dict,
    format_dict,
    columns_list,
    content_list,
    path("build notes table svg"),
    artifact_id,
)

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
        path("build notes table svg"),
        symbol.get("instance_name"),
    )
