import os
import json
from harnice import fileio
import runpy

signals_list_instructions_default = """
from harnice import icd

ch_type_ids = {
    "in": 1,
    "out": 4,
    "shield": 5
}

ch_type_id_supplier = "public"

xlr_pinout = {
    "pos": 2,
    "neg": 3,
    "shield": 1
}

connector_mpns = {
    "XLR3F": ["in1", "in2"],
    "XLR3M": ["out1", "out2"]
}

def mpn_for_connector(connector_name):
    for mpn, conn_list in connector_mpns.items():
        if connector_name in conn_list:
            return mpn
    return None

icd.new_signals_list()

for connector_name in ["in1", "in2", "out1", "out2"]:
    if connector_name.startswith("in"):
        channel_type_id = ch_type_ids["in"]
    elif connector_name.startswith("out"):
        channel_type_id = ch_type_ids["out"]
    else:
        continue

    channel_name = connector_name
    connector_mpn = mpn_for_connector(connector_name)

    for signal in icd.signals_of_channel_type(channel_type_id, ch_type_id_supplier):
        icd.write_signal(
            channel=channel_name,
            channel_type_id=channel_type_id,
            compatible_channel_type_ids=icd.compatible_channel_types(channel_type_id, ch_type_id_supplier),
            signal=signal,
            connector_name=connector_name,
            connector_mpn=connector_mpn,
            contact=xlr_pinout.get(signal)
        )

    # Add shield row
    icd.write_signal(
        channel=f"{channel_name}-shield",
        channel_type_id=ch_type_ids["shield"],
        compatible_channel_type_ids=icd.compatible_channel_types(ch_type_ids["shield"], ch_type_id_supplier),
        signal="shield",
        connector_name=connector_name,
        connector_mpn=connector_mpn,
        contact=xlr_pinout.get("shield")
    )

"""

# Fixed missing closing braces
box_definition_json_default = """
{
    "connectors": {
        "J1": { "mpn": "DB9_F" },
        "J2": { "mpn": "DB9_F" },
        "J3": { "mpn": "DB9_F" },
        "J4": { "mpn": "DB9_F" },
        "J5": { "mpn": "DB9_F" },
        "J6": { "mpn": "DB9_F" }
    },
    "channels": {
        "ch1.chassis": { "channel_type_id": 1, "supplier": "public" },
        "excite": { "channel_type_id": 2, "supplier": "public" },
        "output": { "channel_type_id": 3, "supplier": "public" }
    }
}
"""

def render():
    fileio.verify_revision_structure()

    # Create signals list instructions file if no list.
    if not os.path.exists(fileio.path("signals list")):
        with open(fileio.path("signals list instructions"), "w", encoding="utf-8") as f:
            f.write(signals_list_instructions_default)

    # Run the signals list instructions script
    if os.path.exists(fileio.path("signals list instructions")):
        runpy.run_path(fileio.path("signals list instructions"))
        print("Successfully rebuilt signals list per instructions.")

    # Create box definition JSON if missing
    if not os.path.exists(fileio.path("box definition json")):
        with open(fileio.path("box definition json"), "w", encoding="utf-8") as f:
            f.write(box_definition_json_default)

    # === Validation placeholders ===
    try:
        with open(fileio.path("box definition json"), "r", encoding="utf-8") as f:
            json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid box definition JSON: {e}")

    if not os.path.exists(fileio.path("signals list")):
        raise FileNotFoundError("Signals list was not generated.")

