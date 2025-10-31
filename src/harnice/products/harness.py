import runpy
import os
from harnice import fileio, cli, state
from harnice.lists import instances_list, library_history

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
        parent_csys = instances_list.instance_in_connector_group_with_item_type(instance.get("connector_group"), "backshell")
        parent_csys_outputcsys_name = "connector"
        if parent_csys == 0:
            parent_csys = instances_list.instance_in_connector_group_with_item_type(instance.get("connector_group"), "node")
            parent_csys_outputcsys_name = "origin"

    elif instance.get("item_type") == "backshell":
        parent_csys = instances_list.instance_in_connector_group_with_item_type(instance.get("connector_group"), "node")
        parent_csys_outputcsys_name = "origin"
    else:
        continue

    instances_list.modify(instance.get("instance_name"), {
        "parent_csys_instance_name": parent_csys.get("instance_name"),
        "parent_csys_outputcsys_name": parent_csys_outputcsys_name
    })

feature_tree_utils.update_translate_content()

#===========================================================================
#                   ASSIGN CONDUCTORS
#===========================================================================
#assume the only existing ports at this point are cavities 0 and 1

for instance in fileio.read_tsv("instances list"):
    if instance.get("item_type") == "circuit":
        circuit_id = instance.get("circuit_id")
        conductor_name = f"conductor-{circuit_id}"
        instances_list.new_instance(conductor_name, {
            "item_type": "Conductor",
            "location_type": "segment",
            "node_at_end_a": circuit_utils.instance_of_circuit_port_number(circuit_id, 0),
            "node_at_end_b": circuit_utils.instance_of_circuit_port_number(circuit_id, 1)
        })
        circuit_utils.squeeze_instance_between_ports_in_circuit(conductor_name, instance.get("circuit_id"), 1)

#===========================================================================
#                   UPDATE FORMBOARD DATA
#===========================================================================
formboard_utils.validate_nodes()

for instance in fileio.read_tsv("instances list"):
    if instance.get("item_type") == "Conductor":
        formboard_utils.map_instance_to_segments(instance)

for instance in fileio.read_tsv("instances list"):
    if instance.get("item_type") == "Conductor":
        conductor_length = 0
        for instance2 in fileio.read_tsv("instances list"):
            if instance2.get("parent_instance") == instance.get("instance_name"):
                if instance2.get("length", "").strip():
                    conductor_length += int(instance2.get("length").strip())
        instances_list.modify(instance.get("instance_name"), {"length": conductor_length})

for instance in fileio.read_tsv("instances list"):
    if instance.get("item_type") == "cable":
        cable_length = 0
        for instance2 in fileio.read_tsv("instances list"):
            if instance2.get("parent_instance") == instance.get("instance_name"):
                child_length = int(instance2.get("length", "").strip())
                if child_length > cable_length:
                    cable_length = child_length
        instances_list.modify(instance.get("instance_name"), {"length": cable_length})

formboard_utils.generate_node_coordinates()
formboard_utils.make_segment_drawings()

#===========================================================================
#                   ASSIGN BOM LINE NUMBERS
#===========================================================================
instances_list.assign_bom_line_numbers()


#===========================================================================
#                   ASSIGN PRINT NAMES
#===========================================================================
for instance in fileio.read_tsv("instances list"):
    if instance.get("print_name") not in ["", None]:
        pass
    else:
        if instance.get("item_type") == "connector cavity":
            instance_name = instance.get("instance_name", "")
            print_name = instance_name.split(".")[-1] if "." in instance_name else instance_name
            instances_list.modify(instance_name, {"print_name": print_name})
        elif instance.get("item_type") == "Conductor":
            instances_list.modify(instance.get("instance_name"), {
                "print_name": f"{instance.get("cable_identifier")}"
            })
        else:
            instances_list.modify(instance.get("instance_name"), {
                "print_name": instance.get("instance_name")
                })


#===========================================================================
#                   ASSIGN FLAGNOTES
#===========================================================================
flagnote_counter = 1
buildnote_counter = 1

manual_flagnotes_list.ensure_exists()
for manual_note in fileio.read_tsv("flagnotes manual"):
    affected_list = manual_note.get("affectedinstances", "").strip().split(",")
    for affected in affected_list:
        instances_list.new_instance(f"flagnote-{flagnote_counter}", {
            "item_type": "flagnote",
            "note_type": manual_note.get("note_type"),
            "mpn": manual_note.get("shape"),
            "lib_repo": manual_note.get("shape_lib_repo"),
            "bubble_text": buildnote_counter,
            "parent_instance": affected,
            "connector_group": instances_list.attribute_of(affected, "connector_group"),
            "parent_csys_instance_name": affected,
            "note_text": manual_note.get("note_text")
        })
        flagnote_counter += 1
    if manual_note.get("note_type") == "buildnote":
        buildnote_counter += 1

for rev_row in fileio.read_tsv("revision history"):
    affected_raw = rev_row.get("affectedinstances", "").strip()
    if affected_raw:
        for affected in [a.strip() for a in affected_raw.split(",") if a.strip()]:
            instances_list.new_instance(f"flagnote-{flagnote_counter}", {
                "item_type": "flagnote",
                "note_type": "rev_change_callout",
                "mpn": "rev_change_callout",
                "lib_repo": "https://github.com/kenyonshutt/harnice-library-public",
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
            "lib_repo": "https://github.com/kenyonshutt/harnice-library-public",
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
            "lib_repo": "https://github.com/kenyonshutt/harnice-library-public",
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
                "note_type": "buildnote",
                "mpn": "buildnote",
                "lib_repo": "https://github.com/kenyonshutt/harnice-library-public",
                "bubble_text": buildnote_counter,
                "parent_instance": instance.get("parent_instance"),
                "parent_csys_instance_name": instance.get("parent_instance"),
                "note_text": "Special cavitiesused in this connector. Refer to wirelist for details"
            })
            flagnote_counter += 1
            cavity_flagnote_conversion_happened = True
if cavity_flagnote_conversion_happened:
    buildnote_counter += 1

flagnote_utils.assign_output_csys()
feature_tree_utils.update_translate_content()
flagnote_utils.compile_buildnotes()

for instance in fileio.read_tsv("instances list"):
    if instance.get("absolute_rotation") not in ["", None]:
        instances_list.modify(instance.get("instance_name"), {
            "rotate_csys": instance.get("absolute_rotation")
        })
"""


def file_structure(item_type=None, instance_name=None):
    return {
        f"{state.partnumber('pn-rev')}-feature_tree.py": "feature tree",
        f"{state.partnumber('pn-rev')}-instances_list.tsv": "instances list",
        f"{state.partnumber('pn-rev')}-formboard_graph_definition.png": "formboard graph definition png",
        f"{state.partnumber('pn-rev')}-library_import_history.tsv": "library history",
        "instance_data": {
            "imported_instances": {
                item_type: {instance_name: {"library_used_do_not_edit": {}}}
            },
            "generated_instances_do_not_edit": {},
        },
        "interactive_files": {
            f"{state.partnumber('pn-rev')}.formboard_graph_definition.tsv": "formboard graph definition",
            f"{state.partnumber('pn-rev')}.flagnotes.tsv": "flagnotes manual",
        },
    }


def generate_structure():
    os.makedirs(
        fileio.dirpath("instance_data", structure_dict=file_structure()), exist_ok=True
    )
    os.makedirs(
        fileio.dirpath("imported_instances", structure_dict=file_structure()),
        exist_ok=True,
    )
    fileio.silentremove(
        fileio.dirpath(
            "generated_instances_do_not_edit", structure_dict=file_structure()
        )
    )
    os.makedirs(
        fileio.dirpath(
            "generated_instances_do_not_edit", structure_dict=file_structure()
        ),
        exist_ok=True,
    )
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
            build_macro_contents = f'feature_tree_utils.run_macro(\n    "{build_macro_name}",\n    "harness_builder",\n    "https://github.com/kenyonshutt/harnice-library-public",\n    "harness-from-system-1",\n    system_pn_rev=["{system_pn}","{system_rev}"],\n    path_to_system_rev=os.path.join("{path_to_system_pn}", "{system_pn}-{system_rev}"),\n    target_net="{target_net}",\n    manifest_nets=["{target_net}"]\n)'
            push_harness_instances_list_to_upstream_system = f'post_harness_instances_list.push("{path_to_system_pn}", ("{system_pn}","{system_rev}"))'

        else:
            print(
                "Unrecognized input. If you meant to select a template not listed, just select a template, delete the contents and start over manually. rip."
            )
            render()

        if output_macro_dict is None:
            output_macro_contents = """feature_tree_utils.run_macro("bom_exporter_bottom_up", "harness_artifacts", "https://github.com/kenyonshutt/harnice-library-public", artifact_id="bom-1")
feature_tree_utils.run_macro("standard_harnice_formboard", "harness_artifacts", "https://github.com/kenyonshutt/harnice-library-public", artifact_id="formboard-1", scale=scales.get("A"))
feature_tree_utils.run_macro("circuit_visualizer", "harness_artifacts", "https://github.com/kenyonshutt/harnice-library-public", artifact_id="circuitviz-1")
feature_tree_utils.run_macro("revision_history_table", "harness_artifacts", "https://github.com/kenyonshutt/harnice-library-public", artifact_id="revhistory-1")
feature_tree_utils.run_macro("buildnotes_table", "harness_artifacts", "https://github.com/kenyonshutt/harnice-library-public", artifact_id="buildnotestable-1")
feature_tree_utils.run_macro("pdf_generator", "harness_artifacts", "https://github.com/kenyonshutt/harnice-library-public", artifact_id="pdf_drawing-1", scales=scales)"""
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

    cli.print_import_headers()
    runpy.run_path(fileio.path("feature tree"), run_name="__main__")

    print(f"Harnice: harness {state.partnumber('pn')} rendered successfully!\n")
