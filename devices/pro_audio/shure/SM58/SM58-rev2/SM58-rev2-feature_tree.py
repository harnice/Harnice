
from harnice import icd

ch_type_ids = {
    "in": (1, "public"),
    "out": (4, "public"),
    "chassis": (5, "public")
}

xlr_pinout = {
    "pos": 2,
    "neg": 3,
    "chassis": 1
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

    for signal in icd.signals_of_channel_type_id(channel_type_id):
        icd.write_signal(
            channel=channel_name,
            signal=signal,
            connector_name=connector_name,
            contact=xlr_pinout.get(signal),
            channel_type_id=channel_type_id,
            connector_mpn=connector_mpn
        )

    # Add shield row
    icd.write_signal(
        channel=f"{channel_name}-shield",
        signal="chassis",
        connector_name=connector_name,
        contact=xlr_pinout.get("chassis"),
        channel_type_id=ch_type_ids["chassis"],
        connector_mpn=connector_mpn
    )

