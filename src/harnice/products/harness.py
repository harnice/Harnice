import runpy
import os
from harnice import fileio, cli, state
from harnice.lists import instances_list, library_history

default_desc = "HARNESS, DOES A, FOR B"


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
    """
    Main harness rendering entrypoint.
    """

    feature_tree_path = fileio.path("feature tree", structure_dict=file_structure())

    # ======================================================================
    # 1. Feature tree does not exist: prompt user and create it
    # ======================================================================
    if not os.path.exists(feature_tree_path):

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
            build_macro_block = default_build_macro_block(system_pn, system_rev, target_net)
            push_block = default_push_block()

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
        feature_tree_text = _make_feature_tree(build_macro_block, push_block)

        with open(feature_tree_path, "w", encoding="utf-8") as f:
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


# ======================================================================
# Helper: prompt for system/no-system
# ======================================================================
def _prompt_build_macro():
    print("  's'   Enter 's' for system (or just hit enter) "
          "if this harness is pulling data from a system instances list")
    print("  'n'   Enter 'n' for none to build your harness entirely "
          "out of rules in feature tree (you're hardcore)")
    return cli.prompt("")


# ======================================================================
# Helper: build the complete feature tree file text
# ======================================================================
def _make_feature_tree(build_macro_block: str, push_block: str) -> str:
    """
    Insert build_macro_block and push_block into your exact template.
    """

    return f"""
import os
from harnice import fileio, state
from harnice.utils import (
    circuit_utils,
    formboard_utils,
    note_utils,
    library_utils,
    feature_tree_utils,
)
from harnice.lists import (
    instances_list,
    post_harness_instances_list,
    rev_history,
)

{build_macro_block}

# ===========================================================================
#                  HARNESS BUILD RULES
# ===========================================================================
# example: assign a special contact to one specific conductor
instances = fileio.read_tsv("instances list")
circuit_instance = None
connector_at_end_a = None
for instance in instances:
    if instance.get("channel_group") == "channel-MIC2.out1-PREAMP1.in2":
        if instance.get("signal_of_channel_type") == "pos":
            if instance.get("item_type") == "circuit":
                circuit_instance = instance
                connector_at_end_a = instances_list.attribute_of(instance.get("node_at_end_a"), "connector_group")
new_instance_name = f"{{circuit_instance.get("instance_name")}}-special_contact"
circuit_id = int(circuit_instance.get("circuit_id"))
instances_list.new_instance(
    new_instance_name, {{
        "bom_line_number": True,
        "mpn": "TXPS20",
        "item_type": "contact",
        "location_type": "node",
        "circuit_id": circuit_id,
        "connector_group": connector_at_end_a
    }}
)
circuit_utils.squeeze_instance_between_ports_in_circuit(
    new_instance_name, circuit_id, 1
)

# example: add a backshell
for instance in instances:
    if instance.get("instance_name") in ["X1.B.conn", "PREAMP2.in2.conn"]:
        instances_list.new_instance(f"{{instance.get("connector_group")}}.bs", {{
            "bom_line_number": True,
            "mpn": "M85049-90_9Z03",
            "item_type": "backshell",
            "parent_instance": instance.get("instance_name"),
            "location_type": "node",
            "connector_group": instance.get("connector_group"),
            "parent_csys_instance_name": (instances_list.instance_in_connector_group_with_item_type(instance.get("connector_group"), "node")).get("instance_name"),
            "parent_csys_outputcsys_name": "origin",
            "lib_repo": "https://github.com/harnice/harnice-library-public"
        }})
        instances_list.modify(instance.get("instance_name"), {{
            "parent_csys_instance_name": f"{{instance.get("connector_group")}}.bs",
            "parent_csys_outputcsys_name": "connector",
        }})


# ===========================================================================
#                   IMPORT PARTS FROM LIBRARY FOR GENERAL USE
# ===========================================================================
for instance in fileio.read_tsv("instances list"):
    if instance.get("item_type") in ["connector", "backshell"]:
        if instance.get("instance_name") not in ["X100"]:
            if instance.get("mpn") not in ["TXPA20"]:
                library_utils.pull(instance)

# ===========================================================================
#                  PROCESS HARNESS LAYOUT GRAPH
# ===========================================================================
formboard_utils.validate_nodes()

instances = fileio.read_tsv("instances list")
for instance in instances:
    if instance.get("item_type") == "cable":
        for instance2 in instances:
            if instance2.get("parent_instance") == instance.get("instance_name"):
                if instance2.get("item_type") == "conductor":
                    instances_list.modify(
                        instance.get("instance_name"),
                        {{
                            "node_at_end_a": instances_list.instance_in_connector_group_with_item_type(
                                instances_list.attribute_of(
                                    instance2.get("node_at_end_a"), "connector_group"
                                ),
                                "node",
                            ).get("instance_name"),
                            "node_at_end_b": instances_list.instance_in_connector_group_with_item_type(
                                instances_list.attribute_of(
                                    instance2.get("node_at_end_b"), "connector_group"
                                ),
                                "node",
                            ).get("instance_name"),
                        }},
                    )
                    break

for instance in fileio.read_tsv("instances list"):
    if instance.get("item_type") in ["conductor", "cable", "net-channel"]:
        formboard_utils.map_instance_to_segments(instance)

for instance in fileio.read_tsv("instances list"):
    if instance.get("item_type") in ["conductor", "cable"]:
        length = 0
        for instance2 in fileio.read_tsv("instances list"):
            if instance2.get("parent_instance") == instance.get("instance_name"):
                if instance2.get("length", "").strip():
                    length += int(instance2.get("length").strip())
        instances_list.modify(instance.get("instance_name"), {{"length": length}})

# ===========================================================================
#                   ASSIGN BOM LINE NUMBERS
# ===========================================================================
for instance in fileio.read_tsv("instances list"):
    if instance.get("item_type") in ["connector", "cable", "backshell"]:
        instances_list.modify(instance.get("instance_name"), {{"bom_line_number": True}})
instances_list.assign_bom_line_numbers()

# ===========================================================================
#       ASSIGN PRINT NAMES
# ===========================================================================
for x in range(2):
    for instance in fileio.read_tsv("instances list"):
        if instance.get("item_type") == "connector_cavity":
            instance_name = instance.get("instance_name", "")
            print_name = f"cavity {{instance_name.split(".")[-1] if "." in instance_name else instance_name}}"
            instances_list.modify(instance_name, {{"print_name": print_name}})

        elif instance.get("item_type") in ["conductor", "conductor-segment"]:
            instances_list.modify(instance.get("instance_name"), {{
                "print_name": f"'{{instance.get("cable_identifier")}}' of '{{instances_list.attribute_of(instance.get("cable_group"), "print_name")}}'"
            }})

        elif instance.get("item_type") == "net-channel":
            print_name = f"'{{instance.get("this_net_from_device_channel_id")}}' of '{{instance.get("this_net_from_device_refdes")}}' to '{{instance.get("this_net_to_device_channel_id")}}' of '{{instance.get("this_net_to_device_refdes")}}'"
            instances_list.modify(instance.get("instance_name"), {{"print_name": print_name}})

        elif instance.get("item_type") == "net-channel-segment":
            print_name = f"'{{instances_list.attribute_of(instance.get("parent_instance"), "this_net_from_device_channel_id")}}' of '{{instances_list.attribute_of(instance.get("parent_instance"), "this_net_from_device_refdes")}}' to '{{instances_list.attribute_of(instance.get("parent_instance"), "this_net_to_device_channel_id")}}' of '{{instances_list.attribute_of(instance.get("parent_instance"), "this_net_to_device_refdes")}}'"
            instances_list.modify(instance.get("instance_name"), {{"print_name": print_name}})

        elif instance.get("item_type") == "connector":
            print_name = f"{{instance.get("connector_group")}}"
            instances_list.modify(instance.get("instance_name"), {{"print_name": print_name}})

        elif instance.get("item_type") == "cable-segment":
            print_name = f"{{instance.get("cable_group")}}"
            instances_list.modify(instance.get("instance_name"), {{"print_name": print_name}})

        elif instance.get("item_type") == "contact":
            print_name = instance.get("mpn")
            instances_list.modify(
                instance.get("instance_name"),
                {{"print_name": print_name}}
            )

        else:
            instances_list.modify(instance.get("instance_name"), {{"print_name": instance.get("instance_name")}})

# ===========================================================================
#                  ADD BUILD NOTES
# ===========================================================================
for rev_row in fileio.read_tsv("revision history"):
    if rev_row.get("rev") == state.rev:
        note_utils.make_rev_history_notes(rev_row)

for instance in fileio.read_tsv("instances list"):
    for note in note_utils.get_lib_build_notes(instance):
        note_utils.new_note(
            "build_note",
            note,
            affectedinstances=[instance.get("instance_name")]
        )

note_utils.assign_buildnote_numbers()

# example: add notes to describe actions
# note_utils.new_note(
#     "build_note",
#     "do this",
#     affectedinstances=["X1.B.conn"]
# )
# note_utils.new_note(
#     "build_note",
#     "do that"
# )

# example: combine buildnotes if their texts are similar
#note_utils.combine_notes("Torque backshell to connector at 40 in-lbs","Torque backshell to connector at about 40 in-lbs")


# ===========================================================================
#                  PUT TOGETHER FORMBOARD SVG INSTANCE CONTENT
# ===========================================================================
instances = fileio.read_tsv("instances list")
note_instances = []
for instance in instances:
    if instance.get("item_type") == "note":
        note_instances.append(note_utils.parse_note_instance(instance))

formboard_overview_instances = []
formboard_detail_instances = []
for instance in instances:
    if instance.get("item_type") not in ["connector", "backshell", "segment", "node", "origin"]:
        continue

    formboard_overview_instances.append(instance)
    formboard_detail_instances.append(instance)

    detail_flag_note_counter = 1
    overview_flag_note_counter = 1

    if instance.get("item_type") in ["connector", "backshell"]:
        formboard_detail_instances.append(note_utils.make_bom_flagnote(instance, f"flagnote-{{detail_flag_note_counter}}"))
        detail_flag_note_counter += 1

        formboard_detail_instances.append(note_utils.make_part_name_flagnote(instance, f"flagnote-{{detail_flag_note_counter}}"))
        detail_flag_note_counter += 1

    if instance.get("item_type") == "connector":
        formboard_overview_instances.append(note_utils.make_part_name_flagnote(instance, f"flagnote-{{overview_flag_note_counter}}"))
        overview_flag_note_counter += 1

    for note_instance in note_instances:
        if note_instance.get("note_type") == "build_note":
            if instance.get("instance_name") in note_instance.get("note_affected_instances"):
                formboard_detail_instances.append(
                    note_utils.make_buildnote_flagnote(note_instance, instance, f"flagnote-{{detail_flag_note_counter}}")
                )
                detail_flag_note_counter += 1

        if note_instance.get("note_type") == "rev_change_callout":
            if instance.get("instance_name") in note_instance.get("note_affected_instances"):
                formboard_detail_instances.append(
                    note_utils.make_rev_change_flagnote(note_instance, instance, f"flagnote-{{detail_flag_note_counter}}")
                )
                detail_flag_note_counter += 1

# ===========================================================================
#                  BUILD HARNESS OUTPUTS
# ===========================================================================
instances = fileio.read_tsv("instances list")
scales = {{"A": 0.25, "B": 0.3, "C": 1}}

feature_tree_utils.run_macro(
    "bom_exporter_bottom_up",
    "harness_artifacts",
    "https://github.com/harnice/harnice-library-public",
    artifact_id="bom-1",
)
feature_tree_utils.run_macro(
    "standard_harnice_formboard",
    "harness_artifacts",
    "https://github.com/harnice/harnice-library-public",
    artifact_id="formboard-overview",
    scale=scales.get("A"),
    input_instances=formboard_overview_instances,
)
feature_tree_utils.run_macro(
    "standard_harnice_formboard",
    "harness_artifacts",
    "https://github.com/harnice/harnice-library-public",
    artifact_id="formboard-detail",
    scale=scales.get("C"),
    input_instances=formboard_detail_instances,
)
feature_tree_utils.run_macro(
    "segment_visualizer",
    "harness_artifacts",
    "https://github.com/harnice/harnice-library-public",
    artifact_id="cable_layout-1",
    scale=scales.get("A"),
    item_type="cable-segment",
    segment_spacing_inches=0.1,
)
feature_tree_utils.run_macro(
    "segment_visualizer",
    "harness_artifacts",
    "https://github.com/harnice/harnice-library-public",
    artifact_id="conductor-layout-1",
    scale=scales.get("A"),
    item_type="conductor-segment",
    segment_spacing_inches=0.1,
)
feature_tree_utils.run_macro(
    "segment_visualizer",
    "harness_artifacts",
    "https://github.com/harnice/harnice-library-public",
    artifact_id="channel-layout-1",
    scale=scales.get("B"),
    item_type="net-channel-segment",
    segment_spacing_inches=0.1,
)
feature_tree_utils.run_macro(
    "circuit_visualizer",
    "harness_artifacts",
    "https://github.com/harnice/harnice-library-public",
    artifact_id="circuitviz-1",
    input_circuits=instances,
)
feature_tree_utils.run_macro(
    "revision_history_table",
    "harness_artifacts",
    "https://github.com/harnice/harnice-library-public",
    artifact_id="revhistory-1",
)

build_notes_list_instances = []
for instance in fileio.read_tsv("instances list"):
    if instance.get("item_type") == "note" and instance.get("note_type") == "build_note":
        build_notes_list_instances.append(instance)

feature_tree_utils.run_macro(
    "build_notes_table",
    "harness_artifacts",
    "https://github.com/harnice/harnice-library-public",
    artifact_id="build_notes_table-1",
    input_instances=build_notes_list_instances,
)
feature_tree_utils.run_macro(
    "pdf_generator",
    "harness_artifacts",
    "https://github.com/harnice/harnice-library-public",
    artifact_id="pdf_drawing-1",
    scales=scales,
)

{push_block}

# for convenience, move any pdf to the base directory of the harness
feature_tree_utils.copy_pdfs_to_cwd()
"""


# ======================================================================
# BLOCKS FOR BUILDING THE HARNESS FROM A SYSTEM
# ======================================================================

def default_build_macro_block(system_pn, system_rev, target_net):
    return f"""
# ===========================================================================
#                   build_macro SCRIPTING
# ===========================================================================
system_pn = "{system_pn}" # enter your system part number
system_rev = "{system_rev}" # enter your system revision
system_base_directory = fileio.get_path_to_project(system_pn) # add the path to project_locations.csv in the root of harnice
system_target_net = "{target_net}" # enter the net you're building from

feature_tree_utils.run_macro(
    "import_harness_from_harnice_system",
    "harness_builder",
    "https://github.com/harnice/harnice-library-public",
    "harness-from-system-1",
    system_pn=f"{{system_pn}}",
    system_rev=f"{{system_rev}}",
    path_to_system_rev=os.path.join(
        system_base_directory,
        f"{{system_pn}}-{{system_rev}}",
    ),
    target_net=system_target_net,
    manifest_nets=[system_target_net],
)

rev_history.overwrite(
    {{
        "desc": f"HARNESS '{{system_target_net}}' FROM SYSTEM '{{system_pn}}-{{system_rev}}'",
    }}
)
"""

def default_push_block():
    return """
# ensure the system that this harness was built from contains the complete updated instances list
post_harness_instances_list.push(
    system_base_directory,
    (system_pn, system_rev),
)
"""
