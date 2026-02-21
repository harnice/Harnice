import runpy
import os
from harnice import fileio, state, cli
from harnice.lists import post_harness_instances_list, instances_list, library_history

default_desc = "SYSTEM, SCOPE, etc."

button_color = "#86e1eb"

system_feature_tree_utils_default = """from harnice import fileio
from harnice.utils import system_utils, feature_tree_utils
from harnice.lists import instances_list, manifest, channel_map, circuits_list, disconnect_map

#===========================================================================
#                   KICAD PROCESSING
#===========================================================================
feature_tree_utils.run_macro("kicad_pro_to_bom", "system_builder", "https://github.com/harnice/harnice", artifact_id="bom-1")

#===========================================================================
#                   COLLECT AND PULL DEVICES FROM LIBRARY
#===========================================================================
system_utils.make_instances_from_bom()

#===========================================================================
#                   CHANNEL MAPPING
#===========================================================================
feature_tree_utils.run_macro(
    "kicad_pro_to_system_connector_list",
    "system_builder",
    "https://github.com/harnice/harnice",
    artifact_id="system-connector-list-1"
)
manifest.new()
channel_map.new()

#add manual channel map commands here. key=(from_device_refdes, from_device_channel_id)
#channel_map.map(("MIC3", "out1"), ("PREAMP1", "in2"))

#map channels to other compatible channels by sorting alphabetically then mapping compatibles
feature_tree_utils.run_macro(
    "basic_channel_mapper",
    "system_builder",
    "https://github.com/harnice/harnice",
    artifact_id="channel-mapper-1"
)

#if mapped channels must connect via disconnects, add the list of disconnects to the channel map
system_utils.add_chains_to_channel_map()

#map channels that must pass through disconnects to available channels inside disconnects
disconnect_map.new()

#add manual disconnect map commands here
#disconnect_map.already_assigned_disconnects_set_append(('X1', 'ch0'))

#map channels passing through disconnects to available channels inside disconnects
feature_tree_utils.run_macro(
    "disconnect_mapper",
    "system_builder",
    "https://github.com/harnice/harnice",
    artifact_id="disconnect-mapper-1"
)

# ensure channels that are required to be mapped through disconnects are in fact done so
disconnect_map.ensure_requirements_met()

#process channel and disconnect maps to make a list of every circuit in your system
circuits_list.new()

# ===========================================================================
#                   INSTANCES LIST
# ===========================================================================
system_utils.make_instances_for_connectors_cavities_nodes_channels_circuits()

# assign mating connectors
for instance in fileio.read_tsv("instances list"):
    if instance.get("item_type") == "connector":
        if instance.get("this_instance_mating_device_connector_mpn") == "XLR3M":
            instances_list.modify(
                instance.get("instance_name"),
                {
                    "mpn": "D38999_26ZA98PN",
                    "lib_repo": "https://github.com/harnice/harnice",
                },
            )
        elif instance.get("this_instance_mating_device_connector_mpn") == "XLR3F":
            instances_list.modify(
                instance.get("instance_name"),
                {
                    "mpn": "D38999_26ZB98PN",
                    "lib_repo": "https://github.com/harnice/harnice",
                },
            )
        elif instance.get("this_instance_mating_device_connector_mpn") == "DB25M":
            instances_list.modify(
                instance.get("instance_name"),
                {
                    "mpn": "D38999_26ZC35PN",
                    "lib_repo": "https://github.com/harnice/harnice",
                },
            )
        elif instance.get("this_instance_mating_device_connector_mpn") == "DB25F":
            instances_list.modify(
                instance.get("instance_name"),
                {
                    "mpn": "D38999_26ZE6PN",
                    "lib_repo": "https://github.com/harnice/harnice",
                },
            )

# ===========================================================================
#                   ASSIGN CONDUCTORS
# ===========================================================================

# add one conductor per circuit
for instance in fileio.read_tsv("instances list"):
    if instance.get("item_type") == "circuit":
        circuit_id = instance.get("circuit_id")
        conductor_name = f"conductor-{circuit_id}"
        instances_list.new_instance(
            conductor_name,
            {
                "net": instance.get("net"),
                "item_type": "conductor",
                "location_type": "segment",
                "channel_group": instance.get("channel_group"),
                "node_at_end_a": circuit_utils.instance_of_circuit_port_number(
                    circuit_id, 0 # assume the only existing ports at this point are cavities at 0 and 1
                ),
                "node_at_end_b": circuit_utils.instance_of_circuit_port_number(
                    circuit_id, 1
                ),
                "this_channel_from_channel_type": instance.get("this_channel_from_channel_type"),
                "this_channel_to_channel_type": instance.get("this_channel_to_channel_type"),
                "signal_of_channel_type": instance.get("signal_of_channel_type")
            },
        )
        circuit_utils.squeeze_instance_between_ports_in_circuit(
            conductor_name, instance.get("circuit_id"), 1
        )

# define the cable types we want to use here
audio_cable = {
    "lib_repo": "https://github.com/harnice/harnice",
    "mpn": "8762 0602000",
    "lib_subpath": "belden",
}

# assign conductors to cable-id
cable_id_counter = 1
instances = fileio.read_tsv("instances list")
for net in instances_list.list_of_uniques("net"):
    for chgroup in instances_list.list_of_uniques("channel_group"):
        for instance in instances:
            cable_name = f"cable-{cable_id_counter}"

            if instance.get("net") != net:
                continue
            if instance.get("channel_group") != chgroup:
                continue
            if instance.get("item_type") != "conductor":
                continue

            if chtype.parse(instance.get("this_channel_from_channel_type")) in chtype.is_or_is_compatible_with((1, 'https://github.com/harnice/harnice')):
                if instance.get("signal_of_channel_type") in ["pos"]:
                    circuit_utils.assign_cable_conductor(
                        cable_name,
                        ("pair_1", "white"),
                        instance.get("instance_name"),
                        audio_cable,
                        instance.get("net")
                    )
                if instance.get("signal_of_channel_type") in ["neg"]:
                    circuit_utils.assign_cable_conductor(
                        cable_name,
                        ("pair_1", "black"),
                        instance.get("instance_name"),
                        audio_cable,
                        instance.get("net")
                    )
        cable_id_counter += 1 # in this system, each channel gets its own cable.

#===========================================================================
#                   SYSTEM DESIGN CHECKS
#===========================================================================
connector_list = fileio.read_tsv("system connector list")
circuits_list = fileio.read_tsv("circuits list")

#check for circuits with no connectors
system_utils.find_connector_with_no_circuit(connector_list, circuits_list)


# ===========================================================================
#                   ADD STYLING AND PRINT NAMES TO CHANNELS
# ===========================================================================
# assign styling to channels
audio_channel_style = {
    "base_color": "#D59A10",
}
shield_channel_style = {
    "base_color": "#4039A1",
}

for instance in fileio.read_tsv("instances list"):
    if instance.get("item_type") in ["channel", "net-channel"]:
        if instance.get("this_channel_from_channel_type") in ["(1, 'https://github.com/harnice/harnice')", "(2, 'https://github.com/harnice/harnice')"]:
            instances_list.modify(
                instance.get("instance_name"),
                {
                    "appearance": audio_channel_style
                }
            )
        if instance.get("this_channel_from_channel_type") == "(5, 'https://github.com/harnice/harnice')":
            instances_list.modify(
                instance.get("instance_name"),
                {
                    "appearance": shield_channel_style
                }
            )

for instance in fileio.read_tsv("instances list"):
    if instance.get("item_type") == "net-channel":
        instances_list.modify(instance.get("instance_name"), {
            "print_name_at_end_a": instance.get("this_net_from_device_channel_id"),
            "print_name_at_end_b": instance.get("this_net_to_device_channel_id")
        })

# ===========================================================================
#                   SYSTEM ARTIFACT GENERATORS
# ===========================================================================

# prepare the channel map block diagram overlay
chmap_instances = []
for instance in fileio.read_tsv("instances list"):
    if instance.get("item_type") == "net-channel":
        chmap_instances.append(instance)
feature_tree_utils.run_macro(
    "kicad_sch_net_overlay",
    "system_artifacts",
    "https://github.com/harnice/harnice",
    artifact_id="blockdiagram-chmap-1",
    item_type="net-channel",
    instances=chmap_instances
)

# for convenience, move any pdf to the base directory of the harness
feature_tree_utils.copy_pdfs_to_cwd()
"""


def file_structure():
    return {
        f"{state.partnumber('pn-rev')}-feature_tree.py": "feature tree",
        f"{state.partnumber('pn-rev')}-instances_list.tsv": "instances list",
        f"{state.partnumber('pn-rev')}-library_import_history.tsv": "library history",
        "instance_data": {},
        "features_for_relatives": {},
        "harnesses": {},
        "lists": {
            f"{state.partnumber('pn-rev')}-bom.tsv": "bom",
            f"{state.partnumber('pn-rev')}-circuits_list.tsv": "circuits list",
            f"{state.partnumber('pn-rev')}-post_harness_instances_list.tsv": "post harness instances list",
            f"{state.partnumber('pn-rev')}-harness_manifest.tsv": "harness manifest",
            f"{state.partnumber('pn-rev')}-system_connector_list.tsv": "system connector list",
            f"{state.partnumber('pn-rev')}-mapped_channels_set.tsv": "mapped channels set",
            f"{state.partnumber('pn-rev')}-mapped_disconnect_channels_set.tsv": "mapped disconnects set",
            f"{state.partnumber('pn-rev')}-mapped_a_channels_through_disconnects_set.tsv": "mapped A-side channels through disconnects set",
        },
        "maps": {
            f"{state.partnumber('pn-rev')}-channel_map.tsv": "channel map",
            f"{state.partnumber('pn-rev')}-disconnect_map.tsv": "disconnect map",
        },
    }


def generate_structure():
    os.makedirs(fileio.dirpath("instance_data"), exist_ok=True)
    os.makedirs(fileio.dirpath("features_for_relatives"), exist_ok=True)
    os.makedirs(fileio.dirpath("harnesses"), exist_ok=True)
    os.makedirs(fileio.dirpath("lists"), exist_ok=True)
    os.makedirs(fileio.dirpath("maps"), exist_ok=True)
    pass


def render():
    state.set_net(None)

    if not os.path.exists(fileio.path("feature tree")):
        with open(fileio.path("feature tree"), "w", encoding="utf-8") as f:
            f.write(system_feature_tree_utils_default)

    library_history.new()
    instances_list.new()
    cli.print_import_status_headers()
    runpy.run_path(fileio.path("feature tree"))

    post_harness_instances_list.rebuild()

    print("\nSystem rendered successfully!\n")
