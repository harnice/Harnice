import runpy
import os
from harnice import fileio
from harnice.lists import post_harness_instances_list, instances_list

system_feature_tree_utils_default = """from harnice import fileio
from harnice.utils import system_utils, feature_tree_utils
from harnice.lists import instances_list, manifest, channel_map, circuits_list, disconnect_map

#===========================================================================
#                   KICAD PROCESSING
#===========================================================================
feature_tree_utils.run_macro("kicad_sch_to_pdf", "system_artifacts", "https://github.com/kenyonshutt/harnice-library-public", artifact_id="blockdiagram-1")
feature_tree_utils.run_macro("kicad_pro_to_bom", "system_builder", "https://github.com/kenyonshutt/harnice-library-public", artifact_id="bom-1")

#===========================================================================
#                   COLLECT AND PULL DEVICES FROM LIBRARY
#===========================================================================
system_utils.make_instances_from_bom()

#===========================================================================
#                   CHANNEL MAPPING
#===========================================================================
feature_tree_utils.run_macro("kicad_pro_to_system_connector_list", "system_builder", "https://github.com/kenyonshutt/harnice-library-public", artifact_id="system-connector-list-1")
manifest.new()
channel_map.new()

#add manual channel map commands here. key=(from_device_refdes, from_device_channel_id)
#channel_map.map(("MIC3", "out1"), ("PREAMP1", "in2"))

#map channels to other compatible channels by sorting alphabetically then mapping compatibles
feature_tree_utils.run_macro("basic_channel_mapper", "system_builder", "https://github.com/kenyonshutt/harnice-library-public", artifact_id="channel-mapper-1")

#if mapped channels must connect via disconnects, add the list of disconnects to the channel map
system_utils.add_shortest_disconnect_chain_to_channel_map()

#map channels that must pass through disconnects to available channels inside disconnects
disconnect_map.new()

#add manual disconnect map commands here
#disconnect_map.already_assigned_disconnects_set_append(('X1', 'ch0'))

#map channels passing through disconnects to available channels inside disconnects
feature_tree_utils.run_macro("disconnect_mapper", "system_builder", "https://github.com/kenyonshutt/harnice-library-public", artifact_id="disconnect-mapper-1")

#process channel and disconnect maps to make a list of every circuit in your system
circuits_list.new()

#===========================================================================
#                   INSTANCES LIST
#===========================================================================
system_utils.make_instances_for_connectors_cavities_nodes_channels_circuits()

#assign mating connectors
#for instance in fileio.read_tsv("instances list"):
    #if instance.get("item_type") == "connector":
        #if instance.get("this_instance_mating_device_connector_mpn") == "XLR3M":
            #instances_list.modify(instance.get("instance_name"),{
                #"mpn":"D38999_26ZA98PN",
                #"lib_repo":"https://github.com/kenyonshutt/harnice-library-public"
            #})

#===========================================================================
#                   SYSTEM DESIGN CHECKS
#===========================================================================
connector_list = fileio.read_tsv("system connector list")
circuits_list = fileio.read_tsv("circuits list")

#check for circuits with no connectors
system_utils.find_connector_with_no_circuit(connector_list, circuits_list)
"""


def file_structure():
    return {
        f"{state.partnumber('pn-rev')}-feature_tree.py": "feature tree",
        f"{state.partnumber('pn-rev')}-instances_list.tsv": "instances list",
        "instance_data": {
            "imported_instances": {
                "disconnect": {},
            },
        },
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
    os.makedirs(fileio.dirpath("imported_instances"), exist_ok=True)
    os.makedirs(fileio.dirpath("features_for_relatives"), exist_ok=True)
    os.makedirs(fileio.dirpath("harnesses"), exist_ok=True)
    os.makedirs(fileio.dirpath("lists"), exist_ok=True)
    os.makedirs(fileio.dirpath("maps"), exist_ok=True)
    pass


def render():
    fileio.set_file_structure(file_structure())
    fileio.verify_revision_structure(product_type="system")
    generate_structure()
    if not os.path.exists(fileio.path("feature tree")):
        with open(fileio.path("feature tree"), "w", encoding="utf-8") as f:
            f.write(system_feature_tree_utils_default)

    instances_list.new()
    runpy.run_path(fileio.path("feature tree"))

    post_harness_instances_list.rebuild()

    print("\nSystem rendered successfully!\n")
