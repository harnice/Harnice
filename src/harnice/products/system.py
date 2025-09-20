from harnice import fileio
import runpy
import os

system_feature_tree_default = """from harnice import featuretree_utils, system_utils, instances_list

#===========================================================================
#                   KICAD PROCESSING
#===========================================================================
featuretree_utils.run_macro("kicad_pro_to_netlist_build_macro", "https://github.com/kenyonshutt/harnice-library-public", lib_subpath="build_macros")
featuretree_utils.run_macro("kicad_pro_to_bom_build_macro", "https://github.com/kenyonshutt/harnice-library-public", lib_subpath="build_macros")


#===========================================================================
#                   LIBRARY IMPORTING
#===========================================================================
system_utils.pull_devices_from_library()


#===========================================================================
#                   CHANNEL MAPPING
#===========================================================================
system_utils.new_channel_map()
featuretree_utils.run_macro("basic_channel_mapper_build_macro", "https://github.com/kenyonshutt/harnice-library-public", lib_subpath="build_macros")

#===========================================================================
#                   INSTANCES LIST
#===========================================================================
instances_list.make_new_list()
instances_list.chmap_to_circuits()
"""

def render():
    fileio.verify_revision_structure(product_type="system")
    if not os.path.exists(fileio.path("feature tree")):
        with open(fileio.path("feature tree"), "w", encoding="utf-8") as f:
            f.write(system_feature_tree_default)

    runpy.run_path(fileio.path("feature tree"))