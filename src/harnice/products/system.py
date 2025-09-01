from harnice import fileio, component_library, mapped_channels
import runpy
import os

system_feature_tree_default = """from harnice import featuretree, system_utils, instances_list

#===========================================================================
#                   KICAD PROCESSING
#===========================================================================
featuretree.runprebuilder("kicad_pro_to_netlist_prebuilder", "public")
featuretree.runprebuilder("kicad_pro_to_bom_prebuilder", "public")


#===========================================================================
#                   LIBRARY IMPORTING
#===========================================================================
system_utils.pull_devices_from_library()


#===========================================================================
#                   CHANNEL MAPPING
#===========================================================================
system_utils.new_channel_map()
featuretree.runprebuilder("basic_channel_mapper_prebuilder", "public")

#===========================================================================
#                   INSTANCES LIST
#===========================================================================
instances_list.make_new_list()
instances_list.chmap_to_circuits()
"""

def render():
    fileio.verify_revision_structure()
    if not os.path.exists(fileio.path("feature tree")):
        with open(fileio.path("feature tree"), "w", encoding="utf-8") as f:
            f.write(system_feature_tree_default)

    runpy.run_path(fileio.path("feature tree"))