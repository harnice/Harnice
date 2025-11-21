import runpy
import os
from harnice import fileio, cli, state
from harnice.lists import instances_list, library_history

default_desc = "HARNESS, DOES A, FOR B"

harness_feature_tree_utils_default = """
#===========================================================================
#                   IMPORT PARTS FROM LIBRARY
#===========================================================================
for instance in fileio.read_tsv("instances list"):
    if instance.get("item_type") in ["connector", "backshell"]:
        if instance.get("instance_name") not in ["X100"]:
            if instance.get("mpn") not in ["TXPA20"]:
                library_utils.pull(instance)

#===========================================================================
#                   LOCATE PARTS PER COORDINATE SYSTEMS
#===========================================================================
for instance in fileio.read_tsv("instances list"):
    parent_csys = None
    parent_csys_outputcsys_name = None

    if instance.get("item_type") == "connector":
        parent_csys = instances_list.instance_in_connector_group_with_item_type(
            instance.get("connector_group"), "backshell"
        )
        parent_csys_outputcsys_name = "connector"
        if parent_csys == 0:
            parent_csys = instances_list.instance_in_connector_group_with_item_type(
                instance.get("connector_group"), "node"
            )
            parent_csys_outputcsys_name = "origin"

    elif instance.get("item_type") == "backshell":
        parent_csys = instances_list.instance_in_connector_group_with_item_type(
            instance.get("connector_group"), "node"
        )
        parent_csys_outputcsys_name = "origin"
    else:
        continue

    instances_list.modify(
        instance.get("instance_name"),
        {
            "parent_csys_instance_name": parent_csys.get("instance_name"),
            "parent_csys_outputcsys_name": parent_csys_outputcsys_name,
        },
    )

feature_tree_utils.update_translate_content()


# ===========================================================================
#                   UPDATE FORMBOARD DATA
# ===========================================================================
formboard_utils.validate_nodes()

# each cable ends at the connector at the end nodes of the cable's conductors
instances = fileio.read_tsv("instances list")
for instance in instances:
    if instance.get("item_type") == "cable":
        for instance2 in instances:
            if instance2.get("parent_instance") == instance.get("instance_name"):
                if instance2.get("item_type") == "conductor":
                    instances_list.modify(instance.get("instance_name"), {
                        "node_at_end_a": instances_list.instance_in_connector_group_with_item_type(instances_list.attribute_of(instance2.get("node_at_end_a"), "connector_group"), "node").get("instance_name"),
                        "node_at_end_b": instances_list.instance_in_connector_group_with_item_type(instances_list.attribute_of(instance2.get("node_at_end_b"), "connector_group"), "node").get("instance_name"),
                    })
                    break

# make segment instances for cables, conductors, and channels
for instance in fileio.read_tsv("instances list"):
    if instance.get("item_type") in ["conductor", "cable", "net-channel"]:
        formboard_utils.map_instance_to_segments(instance)

# sum lengths of conductors and cables
for instance in fileio.read_tsv("instances list"):
    if instance.get("item_type") in ["conductor", "cable"]:
        length = 0
        for instance2 in fileio.read_tsv("instances list"):
            if instance2.get("parent_instance") == instance.get("instance_name"):
                if instance2.get("length", "").strip():
                    length += int(instance2.get("length").strip())
        instances_list.modify(
            instance.get("instance_name"), {"length": length}
        )

formboard_utils.generate_node_coordinates()
formboard_utils.make_segment_drawings()

# ===========================================================================
#                   ASSIGN BOM LINE NUMBERS
# ===========================================================================
for instance in fileio.read_tsv("instances list"):
    if instance.get("item_type") in ["connector", "cable", "backshell"]:
        instances_list.modify(instance.get("instance_name"), {"bom_line_number": True})
instances_list.assign_bom_line_numbers()

#===========================================================================
#                   ASSIGN PRINT NAMES
#===========================================================================
for instance in fileio.read_tsv("instances list"):
    if instance.get("print_name") not in ["", None]:
        pass
    else:
        if instance.get("item_type") == "connector_cavity":
            instance_name = instance.get("instance_name", "")
            print_name = f"Cavity {instance_name.split(".")[-1] if "." in instance_name else instance_name}"
            instances_list.modify(instance_name, {"print_name": print_name})
        elif instance.get("item_type") in ["conductor", "conductor-segment"]:
            instances_list.modify(instance.get("instance_name"), {
                "print_name": f"{instance.get("cable_identifier")} of {instances_list.attribute_of(instance.get("parent_instance"), "print_name")}"
            })
        elif instance.get("item_type") == "net-channel":
            print_name = f"'{instance.get("this_net_from_device_channel_id")}' of '{instance.get("this_net_from_device_refdes")}' to '{instance.get("this_net_to_device_channel_id")}' of '{instance.get("this_net_to_device_refdes")}'"
            instances_list.modify(
                instance.get("instance_name"),
                {"print_name": print_name},
            )
        elif instance.get("item_type") == "net-channel-segment":
            print_name = f"'{instances_list.attribute_of(instance.get("parent_instance"), "this_net_from_device_channel_id")}' of '{instances_list.attribute_of(instance.get("parent_instance"), "this_net_from_device_refdes")}' to '{instances_list.attribute_of(instance.get("parent_instance"), "this_net_to_device_channel_id")}' of '{instances_list.attribute_of(instance.get("parent_instance"), "this_net_to_device_refdes")}'"
            instances_list.modify(
                instance.get("instance_name"),
                {"print_name": print_name},
            )
        else:
            instances_list.modify(instance.get("instance_name"), {
                "print_name": instance.get("instance_name")
                })


#===========================================================================
#                   ASSIGN FLAGNOTES
#===========================================================================
flagnote_counter = 1
build_note_counter = 1

for rev_row in fileio.read_tsv("revision history"):
    affected_raw = rev_row.get("affectedinstances", "").strip()
    if affected_raw:
        for affected in [a.strip() for a in affected_raw.split(",") if a.strip()]:
            instances_list.new_instance(f"flagnote-{flagnote_counter}", {
                "item_type": "flagnote",
                "note_type": "rev_change_callout",
                "mpn": "rev_change_callout",
                "lib_repo": "https://github.com/harnice/harnice-library-public",
                "bubble_text": rev_row.get("rev"),
                "parent_instance": affected,
                "connector_group": instances_list.attribute_of(affected, "connector_group"),
                "parent_csys_instance_name": affected
            })
            flagnote_counter += 1

for instance in fileio.read_tsv("instances list"):
    if instance.get("item_type") in ["Cavity", "cable"]:
        continue
    if instance.get("bom_line_number") != "":
        instances_list.new_instance(f"flagnote-{flagnote_counter}", {
            "item_type": "flagnote",
            "note_type": "bom_item",
            "mpn": "bom_item",
            "lib_repo": "https://github.com/harnice/harnice-library-public",
            "bubble_text": instance.get("bom_line_number"),
            "parent_instance": instance.get("instance_name"),
            "connector_group": instances_list.attribute_of(instance.get("instance_name"), "connector_group"),
            "parent_csys_instance_name": instance.get("instance_name")
        })
        flagnote_counter += 1

for instance in fileio.read_tsv("instances list"):
    if instance.get("item_type") in ["connector", "backshell"]:
        bubble_text = instance.get("print_name") or instance.get("instance_name")
        instances_list.new_instance(f"flagnote-{flagnote_counter}", {
            "item_type": "flagnote",
            "note_type": "part_name",
            "mpn": "part_name",
            "lib_repo": "https://github.com/harnice/harnice-library-public",
            "bubble_text": bubble_text,
            "parent_instance": instance.get("instance_name"),
            "connector_group": instances_list.attribute_of(instance.get("instance_name"), "connector_group"),
            "parent_csys_instance_name": instance.get("instance_name")
        })
        flagnote_counter += 1

cavity_flagnote_conversion_happened = False
for instance in fileio.read_tsv("instances list"):
    if instance.get("item_type") == "flagnote":
        if instances_list.attribute_of(instance.get("parent_instance"), "item_type") == "Cavity":
            instances_list.new_instance(f"flagnote-{flagnote_counter}", {
                "item_type": "flagnote",
                "note_type": "build_note",
                "mpn": "build_note",
                "lib_repo": "https://github.com/harnice/harnice-library-public",
                "bubble_text": build_note_counter,
                "parent_instance": instance.get("parent_instance"),
                "parent_csys_instance_name": instance.get("parent_instance"),
                "note_text": "Special cavities used in this connector"
            })
            flagnote_counter += 1
            cavity_flagnote_conversion_happened = True
if cavity_flagnote_conversion_happened:
    build_note_counter += 1

flagnote_utils.assign_output_csys()
feature_tree_utils.update_translate_content()
flagnote_utils.compile_build_notes()

for instance in fileio.read_tsv("instances list"):
    if instance.get("absolute_rotation") not in ["", None]:
        instances_list.modify(instance.get("instance_name"), {
            "rotate_csys": instance.get("absolute_rotation")
        })
"""


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


def render(build_macro="", output_macro_dict=None):
    if not os.path.exists(fileio.path("feature tree", structure_dict=file_structure())):
        if build_macro == "":
            print(
                "  's'   Enter 's' for system (or just hit enter) if this harness is pulling data from a system instances list"
            )
            print(
                "  'n'   Enter 'n' for none to build your harness entirely out of rules in feature tree (you're hardcore)"
            )
            build_macro = cli.prompt("")

        if build_macro in (None, "", "s"):
            build_macro_name = "import_harness_from_harnice_system"
            system_pn = cli.prompt("Enter the system part number")
            system_rev = cli.prompt("Enter the system revision id (ex. rev1)")
            project_location_key = cli.prompt(
                "Make sure project_locations contains a link to the local path of this system. Enter the traceable key",
                default=system_pn,
            )
            target_net = cli.prompt("Enter the net you want to build this harness from")

            path_to_system_pn = fileio.get_path_to_project(project_location_key)
            build_macro_contents = f"""system_pn_rev = ["{system_pn}","{system_rev}"]
target_net = "{target_net}"
feature_tree_utils.run_macro(            
    "{build_macro_name}",
    "harness_builder",
    "https://github.com/harnice/harnice-library-public",
    "harness-from-system-1",
    system_pn_rev=system_pn_rev,
    path_to_system_rev=os.path.join("{path_to_system_pn}", 
    f"{{system_pn_rev[0]}}-{{system_pn_rev[1]}}"),
    target_net=target_net,
    manifest_nets=[target_net]
)
rev_history.overwrite({{
    "desc": f"HARNESS '{{target_net}}' FROM SYSTEM '{{system_pn_rev[0]}}-{{system_pn_rev[1]}}'",
}})
"""
            push_harness_instances_list_to_upstream_system = f'post_harness_instances_list.push("{path_to_system_pn}", ("{system_pn}","{system_rev}"))'

        else:
            print(
                "Unrecognized input. If you meant to select a template not listed, just select a template, delete the contents and start over manually. rip."
            )
            render()

        if output_macro_dict is None:
            output_macro_contents = """feature_tree_utils.run_macro("bom_exporter_bottom_up", "harness_artifacts", "https://github.com/harnice/harnice-library-public", artifact_id="bom-1")
feature_tree_utils.run_macro("standard_harnice_formboard", "harness_artifacts", "https://github.com/harnice/harnice-library-public", artifact_id="formboard-1", scale=scales.get("A"))
circuitviz_1_instances = []
for instance in fileio.read_tsv("instances list"):
    circuitviz_1_instances.append(instance)
feature_tree_utils.run_macro(
    "circuit_visualizer",
    "harness_artifacts",
    "https://github.com/harnice/harnice-library-public",
    artifact_id="circuitviz-1",
    input_circuits = circuitviz_1_instances
)
feature_tree_utils.run_macro("revision_history_table", "harness_artifacts", "https://github.com/harnice/harnice-library-public", artifact_id="revhistory-1")
feature_tree_utils.run_macro("build_notes_table", "harness_artifacts", "https://github.com/harnice/harnice-library-public", artifact_id="build_notestable-1")
feature_tree_utils.run_macro("pdf_generator", "harness_artifacts", "https://github.com/harnice/harnice-library-public", artifact_id="pdf_drawing-1", scales=scales)
feature_tree_utils.run_macro("segment_visualizer","harness_artifacts","https://github.com/harnice/harnice-library-public",artifact_id="cable_layout-1",scale=scales.get("A"),item_type="cable-segment",segment_spacing_inches=0.2,
)"""
        else:
            output_macro_contents = "\n".join(output_macro_dict)

        feature_tree_utils = f"""import os
import yaml
import re
import runpy
from harnice import fileio
from harnice.utils import system_utils, circuit_utils, formboard_utils, svg_utils, flagnote_utils, library_utils, feature_tree_utils
from harnice.lists import instances_list, post_harness_instances_list, rev_history

#===========================================================================
#                   build_macro SCRIPTING
#===========================================================================
{build_macro_contents}

#===========================================================================
#                  HARNESS BUILD RULES
#===========================================================================
{harness_feature_tree_utils_default}

#===========================================================================
#                  CONSTRUCT HARNESS ARTIFACTS
#===========================================================================
scales = {{
    "A": 1
}}

{output_macro_contents}
{push_harness_instances_list_to_upstream_system}
feature_tree_utils.copy_pdfs_to_cwd()
"""

        with open(fileio.path("feature tree"), "w", encoding="utf-8") as dst:
            dst.write(feature_tree_utils)

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

    cli.print_import_status_headers()
    runpy.run_path(fileio.path("feature tree"), run_name="__main__")

    print(f"Harnice: harness {state.partnumber('pn')} rendered successfully!\n")
