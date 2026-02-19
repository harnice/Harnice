import runpy
import os
from harnice import fileio, cli, state
from harnice.lists import instances_list, library_history
from harnice.utils import feature_tree_utils

default_desc = "HARNESS, DOES A FOR B"

documentation_description = "A harness is an assembly of connectors, cables, and other electrical components that connect multiple devices together. It is the physical item that is built and installed in a system."


def file_structure():
    return {
        f"{state.partnumber('pn-rev')}-feature_tree.py": "feature tree",
        f"{state.partnumber('pn-rev')}-instances_list.tsv": "instances list",
        f"{state.partnumber('pn-rev')}-formboard_graph_definition.png": "formboard graph definition png",
        f"{state.partnumber('pn-rev')}-library_import_history.tsv": "library history",
        "interactive_files": {
            f"{state.partnumber('pn-rev')}.formboard_graph_definition.tsv": "formboard graph definition",
        },
    }


def generate_structure():
    os.makedirs(
        fileio.dirpath("interactive_files", structure_dict=file_structure()),
        exist_ok=True,
    )


def render():
    # ======================================================================
    # 1. Feature tree does not exist: prompt user and create it
    # ======================================================================
    if not os.path.exists(fileio.path("feature tree", structure_dict=file_structure())):
        # ------------------------------------------------------------------
        # Ask whether this harness pulls from a system or not
        # ------------------------------------------------------------------
        print(
            "  's'   Enter 's' for system (or just hit enter) "
            "if this harness is pulling data from a system instances list"
        )
        print(
            "  'n'   Enter 'n' for none to build your harness entirely "
            "out of rules in feature tree (you're hardcore)"
        )
        build_macro = cli.prompt("")

        # ------------------------------------------------------------------
        # If harness is built from a system, ask for system parameters
        # ------------------------------------------------------------------
        if build_macro in (None, "", "s"):
            system_pn = cli.prompt("Enter the system part number")
            system_rev = cli.prompt("Enter the system revision id (ex. rev1)")
            target_net = cli.prompt("Enter the net you want to build this harness from")

            # Inject actual values into template
            build_macro_block = feature_tree_utils.default_feature_tree_contents(
                "harness_default_build_macro_block.py",
                replacements={
                    "system_pn": system_pn,
                    "system_rev": system_rev,
                    "target_net": target_net,
                },
            )
            push_block = feature_tree_utils.default_feature_tree_contents(
                "harness_default_push_block.py"
            )
        # ------------------------------------------------------------------
        # Hardcore mode — no system importing
        # ------------------------------------------------------------------
        elif build_macro == "n":
            build_macro_block = ""
            push_block = ""

        else:
            print(
                "Unrecognized input. If you meant to select a template not listed, "
                "just select a template, delete the contents and start over manually. rip."
            )
            exit()

        # ------------------------------------------------------------------
        # Write feature tree file
        # ------------------------------------------------------------------
        feature_tree_text = feature_tree_utils.default_feature_tree_contents(
            "harness_default_feature_tree.py",
            {
                "build_macro_block": build_macro_block,
                "push_block": push_block,
            }
        )

        with open(fileio.path("feature tree"), "w", encoding="utf-8") as f:
            f.write(feature_tree_text)

    # ======================================================================
    # 2. Init library + instances list
    # ======================================================================
    library_history.new()
    instances_list.new()
    instances_list.new_instance(
        "origin",
        {
            "instance_name": "origin",
            "item_type": "origin",
            "location_type": "node",
        },
    )

    # ======================================================================
    # 3. Run the feature tree
    # ======================================================================
    cli.print_import_status_headers()
    runpy.run_path(feature_tree_path, run_name="__main__")

    print(f"Harnice: harness {state.partnumber('pn')} rendered successfully!\n")
