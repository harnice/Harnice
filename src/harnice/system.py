from harnice import fileio
import runpy
import os
import json
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
system.update_channel_map()
"""

def render():
    if not os.path.exists(fileio.path("system render instructions")):
        with open(fileio.path("system render instructions"), "w", encoding="utf-8") as f:
            f.write(system_render_instructions_default)

    runpy.run_path(fileio.path("system render instructions"))

    fileio.verify_revision_structure()

def read_netlist():
    with open(fileio.path("netlist"), "r", encoding="utf-8") as f:
        return json.load(f)

def update_channel_map():
    with open(fileio.path('channel map'), 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=CHANNEL_MAP_COLUMNS, delimiter='\t')
        writer.writeheader()
        writer.writerows([])

    for instance in read_netlist():
        #do stuff
        pass