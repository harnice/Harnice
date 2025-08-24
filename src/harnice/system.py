from harnice import fileio, component_library
import runpy
import os
import csv
import json

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

system_render_instructions_default = """from harnice import featuretree, system

#===========================================================================
#                   KICAD PROCESSING
#===========================================================================
featuretree.runprebuilder("kicad_pro_to_netlist_prebuilder", "public")
featuretree.runprebuilder("kicad_pro_to_bom_prebuilder", "public")


#===========================================================================
#                   LIBRARY IMPORTING
#===========================================================================
system.pull_boxes_from_library()


#===========================================================================
#                   CHANNEL MAPPING
#===========================================================================
system.new_channel_map()
featuretree.runprebuilder("basic_channel_mapper_prebuilder", "public")
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

def read_signals_list(path):
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        return list(reader)

def read_netlist():
    with open(fileio.path("netlist"), "r", encoding="utf-8") as f:
        return json.load(f)

def new_channel_map():
    channel_map = []
    seen = set()  # track unique rows by tuple key
    netlist = read_netlist()   # load once

    for refdes in read_bom_rows():
        box_ref = refdes.get("box_ref_des")
        if not box_ref:
            continue

        signals_path = os.path.join(
            fileio.dirpath("imported_boxes"),
            box_ref,
            f"{refdes.get('MPN')}-{refdes.get('rev')}-signals-list.tsv"
        )
        if not os.path.exists(signals_path):
            continue

        signals = read_signals_list(signals_path)
        if not signals:
            continue

        for signal in signals:
            channel_id = signal.get("channel", "").strip()
            if not channel_id:
                continue

            connector_name_of_channel = f"{box_ref}:{signal.get('connector_name', '').strip()}"
            connected_connector_group = next(
                (net for net, conns in netlist.items() if connector_name_of_channel in conns),
                None
            )

            row = {
                "connected_connector_group": connected_connector_group,
                "from_box_refdes": box_ref,
                "from_box_channel_id": channel_id,
                "from_channel_type_id":  signal.get("channel_type_id", "").strip(),
                "from_compatible_channel_type_ids":  signal.get("compatible_channel_type_ids", "").strip()
            }

            # create a uniqueness key from row values
            key = (row["connected_connector_group"], row["from_box_refdes"], row["from_box_channel_id"])

            if key not in seen:
                channel_map.append(row)
                seen.add(key)

    with open(fileio.path("channel map"), "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CHANNEL_MAP_COLUMNS, delimiter="\t")
        writer.writeheader()
        writer.writerows(channel_map)


