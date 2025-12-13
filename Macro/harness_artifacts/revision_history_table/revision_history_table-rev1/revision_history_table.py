import os
from harnice import fileio, state
from harnice.lists import rev_history
from harnice.utils import svg_utils, library_utils

artifact_mpn = "revision_history_table"


# =============== PATHS ===================================================================================
def macro_file_structure(rev_id=None):
    return {
        f"{state.partnumber('pn-rev')}-{artifact_id}-master.svg": "revision history table svg",
        "instance_data": {}
    }


if base_directory is None:  # path between cwd and the file structure for this macro
    base_directory = os.path.join("instance_data", "macro", artifact_id)


def path(target_value, rev_id=None):
    return fileio.path(
        target_value,
        structure_dict=macro_file_structure(rev_id),
        base_directory=base_directory,
    )


def dirpath(target_value, rev_id=None):
    # target_value = None will return the root of this macro
    return fileio.dirpath(
        target_value,
        structure_dict=macro_file_structure(rev_id),
        base_directory=base_directory,
    )

# ==========================================================================================================
layout_dict = {
    "origin_corner": "top-right",
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
        "name": "rev",
        "width": 0.35 * 96,
    },
    {
        "name": "update",
        "width": 2.5 * 96,
    },
    {
        "name": "status",
        "width": 0.6 * 96,
    },
    {
        "name": "drawn",
        "width": 0.6 * 96,
    },
    {
        "name": "checked",
        "width": 0.6 * 96,
    },
    {
        "name": "started",
        "width": 0.45 * 96,
    },
    {
        "name": "modified",
        "width": 0.45 * 96,
    },
]

rev_history_table_contents = [
    {
        "format_key": "header",
        "columns": {
            "rev": "REV",
            "update": "UPDATE",
            "status": "STATUS",
            "drawn": "DRAWN",
            "checked": "CHECKED",
            "started": "STARTED",
            "modified": "MODIFIED",
        }
    }
]

# === Read "revision history" TSV ===
symbols_to_build = []

for rev in rev_history.info(all=True):
    if rev.get("affectedinstances") not in ["", None, []]:
        bubble_instance = {
                "instance_name": f"bubble{rev.get('rev')}",
                "item_type": "flagnote",
                "mpn": "rev_change_callout",
                "lib_repo": "https://github.com/harnice/harnice-library-public",
                "note_text": rev.get("rev"),
            }
        rev_history_table_contents.append(
            {
                "format_key": "row_with_bubble",
                "columns": {
                    "rev": bubble_instance,
                    "update": rev.get("revisionupdates"),
                    "status": rev.get("status"),
                    "drawn": rev.get("drawnby"),
                    "checked": rev.get("checkedby"),
                    "started": rev.get("datestarted"),
                    "modified": rev.get("datemodified"),
                }
            }
        )
        symbols_to_build.append(bubble_instance)
    
    else:
        rev_history_table_contents.append(
            {
                "columns": {
                    "rev": rev.get("rev"),
                    "update": rev.get("revisionupdates"),
                    "status": rev.get("status"),
                    "drawn": rev.get("drawnby"),
                    "checked": rev.get("checkedby"),
                    "started": rev.get("datestarted"),
                    "modified": rev.get("datemodified"),
                }
            }
        )

# ============= BUILD TABLE =======================================================================

svg_utils.table(
    layout_dict,
    format_dict,
    columns_list,
    rev_history_table_contents,
    path("revision history table svg"),
    artifact_id
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
    with open(os.path.join(path_to_symbol, f"{symbol.get('instance_name')}-drawing.svg"), "r") as f:
        svg_content = f.read()

    svg_content = svg_content.replace("flagnote-text", symbol.get("note_text"))

    with open(os.path.join(path_to_symbol, f"{symbol.get('instance_name')}-drawing.svg"), "w") as f:
        f.write(svg_content)

    svg_utils.find_and_replace_svg_group(
        os.path.join(path_to_symbol, f"{symbol.get('instance_name')}-drawing.svg"),
        symbol.get("instance_name"),
        path("revision history table svg"),
        symbol.get("instance_name")
    )