import os
import csv
import ast
from harnice import fileio, state
from harnice.utils import svg_utils

artifact_mpn = "tooling_list_exporter"

# ============== SETUP VARIABLES ===============================================
LENGTH_MARGIN = 12


# =============== PATHS ===================================================================================
def macro_file_structure():
    return {
        f"{state.partnumber('pn-rev')}-{artifact_id}.tsv": "tooling list tsv",
        f"{state.partnumber('pn-rev')}-{artifact_id}-master.svg": "tooling list svg",
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

tool_list = []
tool_table_contents = []
seen_tools = set()

# append header row to the table
tool_table_contents.append(
    {
        "format_key": "header",
        "columns": {
            "tool": "REQUIRED TOOLING",
        },
    }
)

for instance in instances:
    tools = instance.get("lib_tools")
    if tools not in ["", None]:
        try:
            parsed_tools = ast.literal_eval(str(tools))
        except (ValueError, SyntaxError):
            continue

        tools_to_add = (
            parsed_tools if isinstance(parsed_tools, list) else [parsed_tools]
        )
        for tool in tools_to_add:
            if tool not in seen_tools:
                seen_tools.add(tool)
                tool_list.append(tool)
                tool_table_contents.append(
                    {
                        "columns": {
                            "tool": tool,
                        }
                    }
                )


# ============= BUILD TABLE ===========================================================
layout_dict = {
    "origin_corner": "bottom-left",
    "build_direction": "up",
}

format_dict = {
    "globals": {
        "font_size": 8,
        "font_family": "Arial, Helvetica, sans-serif",
        "justify": "left"
    },
    "header": {
        "font_weight": "B",
        "fill_color": "lightgray",
        "justify": "center"
    },
}

columns_list = [
    {
        "name": "tool",
        "width": 2 * 96,
    },
]

svg_utils.table(
    layout_dict,
    format_dict,
    columns_list,
    tool_table_contents,
    path("tooling list svg"),
    artifact_id,
)

# ============= WRITE CSV FILE =======================================================================
tooling_list_tsv_path = path("tooling list tsv")
if tool_list:
    with open(
        tooling_list_tsv_path,
        "w",
        newline="",
        encoding="utf-8",
    ) as tsv_file:
        writer = csv.writer(tsv_file, delimiter="\t")
        writer.writerow(["tool_desc"])
        for tool in tool_list:
            writer.writerow([tool])
else:
    fileio.silentremove(tooling_list_tsv_path)
