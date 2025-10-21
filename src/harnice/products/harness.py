import runpy
import os
from harnice import instances_list, fileio, cli

harness_feature_tree_default = """
#===========================================================================
#                   IMPORT PARTS FROM LIBRARY
#===========================================================================
print()
print("Importing parts from library")
print(f'{"ITEM NAME":<24}  STATUS')

for instance in fileio.read_tsv("instances list"):
    instance_name = instance.get("instance_name")
    mpn = instance.get("mpn")

    if instance.get("item_type") in ["Connector", "Backshell"]:
        if instance_name not in ["X100"]:
            if mpn not in ["TXPA20"]:
                component_library.pull_part(instance_name)

#===========================================================================
#                   LOCATE PARTS PER COORDINATE SYSTEMS
#===========================================================================
for instance in fileio.read_tsv("instances list"):
    parent_csys = None
    parent_csys_outputcsys_name = None

    if instance.get("item_type") == "Connector":
        parent_csys = instances_list.instance_in_connector_group_with_item_type(instance.get("connector_group"), "Backshell")
        parent_csys_outputcsys_name = "connector"
        if parent_csys == 0:
            parent_csys = instances_list.instance_in_connector_group_with_item_type(instance.get("connector_group"), "Node")
            parent_csys_outputcsys_name = "origin"

    elif instance.get("item_type") == "Backshell":
        parent_csys = instances_list.instance_in_connector_group_with_item_type(instance.get("connector_group"), "Node")
        parent_csys_outputcsys_name = "origin"
    else:
        continue

    instances_list.modify(instance.get("instance_name"), {
        "parent_csys_instance_name": parent_csys.get("instance_name"),
        "parent_csys_outputcsys_name": parent_csys_outputcsys_name
    })

featuretree_utils.update_translate_content()

#===========================================================================
#                   ASSIGN CONDUCTORS
#===========================================================================
#assume the only existing ports at this point are cavities 0 and 1

for instance in fileio.read_tsv("instances list"):
    if instance.get("item_type") == "Circuit":
        circuit_id = instance.get("circuit_id")
        conductor_name = f"conductor-{circuit_id}"
        instances_list.new_instance(conductor_name, {
            "item_type": "Conductor",
            "location_type": "Segment",
            "node_at_end_a": circuit_instance.instance_of_circuit_port_number(circuit_id, 0),
            "node_at_end_b": circuit_instance.instance_of_circuit_port_number(circuit_id, 1)
        })
        circuit_instance.squeeze_instance_between_ports_in_circuit(conductor_name, instance.get("circuit_id"), 1)

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
    if instance.get("item_type") == "Cable":
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
        if instance.get("item_type") == "Connector cavity":
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

flagnote_utils.ensure_manual_list_exists()
for manual_note in flagnote_utils.read_manual_list():
    affected_list = manual_note.get("affectedinstances", "").strip().split(",")
    for affected in affected_list:
        instances_list.new_instance(f"flagnote-{flagnote_counter}", {
            "item_type": "Flagnote",
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

for rev_row in flagnote_utils.read_revhistory():
    affected_raw = rev_row.get("affectedinstances", "").strip()
    if affected_raw:
        for affected in [a.strip() for a in affected_raw.split(",") if a.strip()]:
            instances_list.new_instance(f"flagnote-{flagnote_counter}", {
                "item_type": "Flagnote",
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
    if instance.get("item_type") in ["Cavity", "Cable"]:
        continue
    if instance.get("bom_line_number") != "":
        instances_list.new_instance(f"flagnote-{flagnote_counter}", {
            "item_type": "Flagnote",
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
    if instance.get("item_type") in ["Connector", "Backshell"]:
        bubble_text = instance.get("print_name") or instance.get("instance_name")
        instances_list.new_instance(f"flagnote-{flagnote_counter}", {
            "item_type": "Flagnote",
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
    if instance.get("item_type") == "Flagnote":
        if instances_list.attribute_of(instance.get("parent_instance"), "item_type") == "Cavity":
            instances_list.new_instance(f"flagnote-{flagnote_counter}", {
                "item_type": "Flagnote",
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
featuretree_utils.update_translate_content()
flagnote_utils.compile_buildnotes()

for instance in fileio.read_tsv("instances list"):
    if instance.get("absolute_rotation") not in ["", None]:
        instances_list.modify(instance.get("instance_name"), {
            "rotate_csys": instance.get("absolute_rotation")
        })
"""


def render(build_macro="", output_macro_dict=None):
    print("Thanks for using Harnice!")

    # Step 1: revision structure
    fileio.verify_revision_structure(product_type="harness")

    # Step 2: Ensure feature tree exists
    if not os.path.exists(fileio.path("feature tree")):
        if build_macro == "":
            print(
                "Do you want to use a build_macro to help build this harness from scratch? [s]"
            )
            print(
                "  's'   Enter 's' for system (or just hit enter) if this harness is pulling data from a system instances list"
            )
            print("  'y'   Enter 'y' for the standard Harnice esch build_macro")
            print(
                "  'n'   Enter 'n' for none to build your harness entirely out of rules in feature tree (you're hardcore)"
            )
            print(
                "  'w'   Enter 'w' for wireviz to use the wireviz-yaml-to-instances-list build_macro"
            )
            build_macro = cli.prompt("")

        if build_macro in (None, "", "s"):
            build_macro_name = "import_harness_from_harnice_system"
            system_pn = cli.prompt("Enter the system part number")
            system_rev = cli.prompt("Enter the system revision id (ex. rev1)")
            project_location_key = cli.prompt(
                "Make sure project_locations contains a link to the local path of this system. Enter the traceable key"
            )
            target_net = cli.prompt("Enter the net you want to build this harness from")

            path_to_system_pn = fileio.get_path_to_project(project_location_key)
            build_macro_contents = f'featuretree_utils.run_macro(\n    "{build_macro_name}",\n    "harness_builder",\n    "https://github.com/kenyonshutt/harnice-library-public",\n    system_pn_rev=["{system_pn}","{system_rev}"],\n    path_to_system_rev=os.path.join("{path_to_system_pn}", "{system_pn}-{system_rev}"),\n    target_net="{target_net}",\n    manifest_nets=["{target_net}"]\n)'
            push_harness_instances_list_to_upstream_system = f'system_utils.push_harness_instances_list_to_upstream_system("{path_to_system_pn}", ("{system_pn}","{system_rev}"))'

        elif build_macro == "n":
            build_macro_name = "import_harnice_esch"
            build_macro_contents = f'featuretree_utils.run_macro("{build_macro_name}", "harness_builder", "https://github.com/kenyonshutt/harnice-library-public")'

        elif build_macro == "w":
            build_macro_name = "import_harness_wireviz_yaml"
            build_macro_contents = f'featuretree_utils.run_macro("{build_macro_name}", "harness_builder", "https://github.com/kenyonshutt/harnice-library-public")'

        else:
            print(
                "Unrecognized input. If you meant to select a template not listed, just select a template, delete the contents and start over manually. rip."
            )
            render()

        if output_macro_dict is None:
            output_macro_contents = """featuretree_utils.run_macro("bom_exporter_bottom_up", "harness_artifacts", "https://github.com/kenyonshutt/harnice-library-public", artifact_id="bom1")
featuretree_utils.run_macro("standard_harnice_formboard", "harness_artifacts", "https://github.com/kenyonshutt/harnice-library-public", artifact_id="formboard1", scale=scales.get("A"))
featuretree_utils.run_macro("circuit_visualizer", "harness_artifacts", "https://github.com/kenyonshutt/harnice-library-public", artifact_id="circuitviz1")
featuretree_utils.run_macro("revision_history_table", "harness_artifacts", "https://github.com/kenyonshutt/harnice-library-public", artifact_id="revhistory1")
featuretree_utils.run_macro("buildnotes_table", "harness_artifacts", "https://github.com/kenyonshutt/harnice-library-public", artifact_id="buildnotestable1")
featuretree_utils.run_macro("pdf_generator", "harness_artifacts", "https://github.com/kenyonshutt/harnice-library-public", artifact_id="drawing1", scales=scales)
"""
        else:
            output_macro_contents = "\n".join(output_macro_dict)

        feature_tree = f"""import os
import yaml
import re
import runpy

from harnice import (
    fileio, instances_list, component_library,
    flagnote_utils, formboard_utils, rev_history, svg_utils, 
    featuretree_utils, system_utils, circuit_instance
)

#===========================================================================
#                   build_macro SCRIPTING
#===========================================================================
{build_macro_contents}

#===========================================================================
#                  HARNESS BUILD RULES
#===========================================================================
{harness_feature_tree_default}

#===========================================================================
#                  CONSTRUCT HARNESS ARTIFACTS
#===========================================================================
scales = {{
    "A": 1
}}

{output_macro_contents}
{push_harness_instances_list_to_upstream_system}
featuretree_utils.copy_pdfs_to_cwd()
"""

        with open(fileio.path("feature tree"), "w", encoding="utf-8") as dst:
            dst.write(feature_tree)

    # Step 3: initialize instances list
    instances_list.make_new_list()
    instances_list.new_instance(
        "origin",
        {
            "instance_name": "origin",
            "item_type": "Origin",
            "location_type": "Node",
        },
    )

    # Step 4: run feature tree
    runpy.run_path(fileio.path("feature tree"), run_name="__main__")

    print(f"Harnice: harness {fileio.partnumber('pn')} rendered successfully!\n")
