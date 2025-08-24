from harnice import fileio, component_library
import runpy
import os
import csv

CHANNEL_MAP_COLUMNS = [
    "connected_connector_group",
    "from_box_refdes",
    "from_box_channel_id",
    "from_channel_type_id",
    "from_compatible_channel_type_ids",
    "to_box_refdes",
    "to_box_channel_id",
    "to_channel_type_id",
    "to_compatible_channel_type_ids"
]

system_render_instructions_default = """
from harnice import featuretree, system
featuretree.runprebuilder("kicad_pro_to_netlist_prebuilder", "public")
featuretree.runprebuilder("kicad_pro_to_bom_prebuilder", "public")
system.pull_boxes_from_library()
"""

def render():
    if not os.path.exists(fileio.path("system render instructions")):
        with open(fileio.path("system render instructions"), "w", encoding="utf-8") as f:
            f.write(system_render_instructions_default)

    runpy.run_path(fileio.path("system render instructions"))

    fileio.verify_revision_structure()

def read_bom_rows():
    with open(fileio.path("bom"), "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        return list(reader)


def pull_boxes_from_library():
    with open(fileio.path('channel map'), 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=CHANNEL_MAP_COLUMNS, delimiter='\t')
        writer.writeheader()
        writer.writerows([])

    imported_boxes = []

    for refdes in read_bom_rows():
        if refdes not in imported_boxes:
            #import box from library

            component_library.pull_item_from_library(
                supplier = refdes["supplier"],
                lib_subpath="boxes/"+refdes["supplier_subpath"],
                mpn=refdes["MPN"],
                destination_directory=os.path.join(fileio.dirpath("imported_boxes"), refdes["box_ref_des"]),
                used_rev=None,
                item_name=refdes["box_ref_des"],
                quiet=False
            )
        imported_boxes.append(refdes)