from harnice import fileio, mapped_channels, mapped_disconnect_channels
import runpy
import os

system_feature_tree_default = """from harnice import featuretree_utils, system_utils, instances_list

#===========================================================================
#                   KICAD PROCESSING
#===========================================================================
featuretree_utils.run_macro("kicad_pro_to_bom", "system_builder", "https://github.com/kenyonshutt/harnice-library-public")
featuretree_utils.run_macro("kicad_pro_to_system_connector_list", "system_builder", "https://github.com/kenyonshutt/harnice-library-public")


#===========================================================================
#                   LIBRARY IMPORTING
#===========================================================================
system_utils.pull_devices_from_library()


#===========================================================================
#                   CHANNEL MAPPING
#===========================================================================
system_utils.new_blank_channel_map()

#add manual channel map commands here. key=(from_device_refdes, from_device_channel_id)
#system_utils.map_and_record({from_key}, {to_key})

#map channels to other compatible channels by sorting alphabetically then mapping compatibles
featuretree_utils.run_macro("basic_channel_mapper", "system_builder", "https://github.com/kenyonshutt/harnice-library-public")

#if mapped channels must connect via disconnects, add the list of disconnects to the channel map
system_utils.find_shortest_disconnect_chain()

#map channels that must pass through disconnects to available channels inside disconnects
system_utils.new_blank_disconnect_map()

#add manual disconnect map commands here

#map channels passing through disconnects to available channels inside disconnects
featuretree_utils.run_macro("disconnect_channel_mapper", "system_builder", "https://github.com/kenyonshutt/harnice-library-public")

#===========================================================================
#                   INSTANCES LIST
#===========================================================================
#process channel and disconnect maps to make a list of every circuit in your system
system_utils.make_circuits_list()

instances_list.make_new_list()
instances_list.chmap_to_circuits()
"""


def render():
    fileio.verify_revision_structure(product_type="system")
    if not os.path.exists(fileio.path("feature tree")):
        with open(fileio.path("feature tree"), "w", encoding="utf-8") as f:
            f.write(system_feature_tree_default)

    # keep track of what we've already mapped
    mapped_channels.new_set()
    mapped_disconnect_channels.new_set()

    runpy.run_path(fileio.path("feature tree"))
