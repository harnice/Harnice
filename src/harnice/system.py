from harnice import fileio, component_library
import runpy
import os
import csv
import json

CHANNEL_MAP_COLUMNS = [
    "merged_net",
    "channel_type_id",
    "compatible_channel_type_ids",
    "from_box_refdes",
    "from_box_channel_id",
    "to_box_refdes",
    "to_box_channel_id",
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
    fileio.verify_revision_structure()
    if not os.path.exists(fileio.path("system render instructions")):
        with open(fileio.path("system render instructions"), "w", encoding="utf-8") as f:
            f.write(system_render_instructions_default)

    runpy.run_path(fileio.path("system render instructions"))

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
            merged_net = next(
                (net for net, conns in netlist.items() if connector_name_of_channel in conns),
                None
            )

            row = {
                "merged_net": merged_net,
                "channel_type_id":  signal.get("channel_type_id", "").strip(),
                "compatible_channel_type_ids":  signal.get("compatible_channel_type_ids", "").strip(),
                "from_box_refdes": box_ref,
                "from_box_channel_id": channel_id
            }

            # create a uniqueness key from row values
            key = (row["merged_net"], row["from_box_refdes"], row["from_box_channel_id"])

            if key not in seen:
                channel_map.append(row)
                seen.add(key)

    with open(fileio.path("channel map"), "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CHANNEL_MAP_COLUMNS, delimiter="\t")
        writer.writeheader()
        writer.writerows(channel_map)

def read_channel_map():
    with open(fileio.path("channel map"), "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        return list(reader)

def map_channel(from_box_refdes, from_box_channel_id, to_box_refdes, to_box_channel_id):
    """
    Connects a channel from (refdes, channel_id) to another (refdes, channel_id).
    Updates the channel map TSV by:
      1. Finding the source row (from_*), setting its to_* fields.
      2. Removing any standalone target row (to_*).
    """
    path = fileio.path("channel map")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Channel map not found at {path}")

    updated_rows = []
    found_source = False
    removed_target = False

    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        fieldnames = reader.fieldnames
        for row in reader:
            # Case 1: update the source row
            if (
                row.get("from_box_refdes") == from_box_refdes
                and row.get("from_box_channel_id") == from_box_channel_id
            ):
                row["to_box_refdes"] = to_box_refdes
                row["to_box_channel_id"] = to_box_channel_id
                found_source = True
                updated_rows.append(row)
                continue

            # Case 2: drop the standalone target row
            if (
                not removed_target
                and row.get("from_box_refdes") == to_box_refdes
                and row.get("from_box_channel_id") == to_box_channel_id
            ):
                removed_target = True
                continue

            updated_rows.append(row)

    # Write updated TSV back
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        writer.writerows(updated_rows)

    return {
        "found_source": found_source,
        "removed_target": removed_target,
    }


