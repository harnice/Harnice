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
feature_tree_utils.run_macro("kicad_sch_to_pdf", "system_artifacts", "https://github.com/kenyonshutt/harnice-library-public", artifact_id="blockdiagram1")
feature_tree_utils.run_macro("kicad_pro_to_bom", "system_builder", "https://github.com/kenyonshutt/harnice-library-public")

#===========================================================================
#                   COLLECT AND PULL DEVICES FROM LIBRARY
#===========================================================================
system_utils.make_instances_from_bom()

#===========================================================================
#                   CHANNEL MAPPING
#===========================================================================
feature_tree_utils.run_macro("kicad_pro_to_system_connector_list", "system_builder", "https://github.com/kenyonshutt/harnice-library-public")
manifest.new()
channel_map.new()

#add manual channel map commands here. key=(from_device_refdes, from_device_channel_id)
#channel_map.map(("MIC3", "out1"), ("PREAMP1", "in2"))

#map channels to other compatible channels by sorting alphabetically then mapping compatibles
feature_tree_utils.run_macro("basic_channel_mapper", "system_builder", "https://github.com/kenyonshutt/harnice-library-public")

#if mapped channels must connect via disconnects, add the list of disconnects to the channel map
system_utils.add_shortest_disconnect_chain_to_channel_map()

#map channels that must pass through disconnects to available channels inside disconnects
disconnect_map.new()

#add manual disconnect map commands here
#disconnect_map.already_assigned_disconnects_set_append(('X1', 'ch0'))

#map channels passing through disconnects to available channels inside disconnects
feature_tree_utils.run_macro("disconnect_mapper", "system_builder", "https://github.com/kenyonshutt/harnice-library-public")

#process channel and disconnect maps to make a list of every circuit in your system
circuits_list.new()

#===========================================================================
#                   INSTANCES LIST
#===========================================================================
system_utils.make_instances_for_connectors_cavities_nodes_channels_circuits()

#assign mating connectors
#for instance in fileio.read_tsv("instances list"):
    #if instance.get("item_type") == "Connector":
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
    return {}


def generate_structure():
    pass


def render():
    fileio.verify_revision_structure(product_type="system")
    if not os.path.exists(fileio.path("feature tree")):
        with open(fileio.path("feature tree"), "w", encoding="utf-8") as f:
            f.write(system_feature_tree_utils_default)

    instances_list.new()
    runpy.run_path(fileio.path("feature tree"))

    post_harness_instances_list.rebuild()

    print("\nSystem rendered successfully!\n")
