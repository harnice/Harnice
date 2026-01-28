from harnice.lists import signals_list
from harnice.products import chtype

ch_type_ids = {
    "in": (1, "https://github.com/harnice/harnice"),
    "out": (4, "https://github.com/harnice/harnice"),
    "chassis": (5, "https://github.com/harnice/harnice"),
}

xlr_pinout = {"pos": 2, "neg": 3, "chassis": 1}

connector_mpns = {"XLR3F": ["in1", "in2"], "XLR3M": ["out1", "out2"]}


def mpn_for_connector(connector_name):
    for mpn, conn_list in connector_mpns.items():
        if connector_name in conn_list:
            return mpn
    return None


signals_list.new()

for connector_name in ["in1", "in2", "out1", "out2"]:
    if connector_name.startswith("in"):
        channel_type = ch_type_ids["in"]
    elif connector_name.startswith("out"):
        channel_type = ch_type_ids["out"]
    else:
        continue

    channel_name = connector_name
    connector_mpn = mpn_for_connector(connector_name)

    for signal in chtype.signals(channel_type):
        signals_list.append(
            channel_id=channel_name,
            signal=signal,
            connector_name=connector_name,
            cavity=xlr_pinout.get(signal),
            channel_type=channel_type,
            connector_mpn=connector_mpn,
        )

    # Add shield row
    signals_list.append(
        channel_id=f"{channel_name}-shield",
        signal="chassis",
        connector_name=connector_name,
        cavity=xlr_pinout.get("chassis"),
        channel_type=ch_type_ids["chassis"],
        connector_mpn=connector_mpn,
    )
