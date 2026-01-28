from harnice.lists import signals_list
from harnice.products import chtype

ch_type_ids = {
    "A": {
        "balanced audio mic level in": (
            1,
            "https://github.com/harnice/harnice",
        ),
        "chassis": (5, "https://github.com/harnice/harnice"),
    },
    "B": {
        "balanced audio mic level out": (
            2,
            "https://github.com/harnice/harnice",
        ),
        "chassis": (5, "https://github.com/harnice/harnice"),
    },
}

cn_mpns = {"A": "DB25F", "B": "DB25M"}

cavity_number = {
    "ch0": {"pos": 24, "neg": 12, "chassis": 25},
    "ch1": {"pos": 10, "neg": 23, "chassis": 11},
    "ch2": {"pos": 21, "neg": 9, "chassis": 22},
    "ch3": {"pos": 7, "neg": 20, "chassis": 8},
    "ch4": {"pos": 18, "neg": 6, "chassis": 19},
    "ch5": {"pos": 4, "neg": 17, "chassis": 5},
    "ch6": {"pos": 15, "neg": 3, "chassis": 16},
    "ch7": {"pos": 1, "neg": 14, "chassis": 2},
}

signals_list.new()

for channel in range(8):
    channel_name = f"ch{channel}"

    for signal in chtype.signals(ch_type_ids["A"]["balanced audio mic level in"]):
        signals_list.append(
            channel_id=channel_name,
            signal=signal,
            A_cavity=cavity_number[channel_name][signal],
            A_connector_mpn=cn_mpns["A"],
            A_channel_type=ch_type_ids["A"]["balanced audio mic level in"],
            B_cavity=cavity_number[channel_name][signal],
            B_connector_mpn=cn_mpns["B"],
            B_channel_type=ch_type_ids["B"]["balanced audio mic level out"],
        )

    for signal in chtype.signals(ch_type_ids["A"]["chassis"]):
        signals_list.append(
            channel_id=f"{channel_name}-shield",
            signal=signal,
            A_cavity=cavity_number[channel_name][signal],
            A_connector_mpn=cn_mpns["A"],
            A_channel_type=ch_type_ids["A"]["chassis"],
            B_cavity=cavity_number[channel_name][signal],
            B_connector_mpn=cn_mpns["B"],
            B_channel_type=ch_type_ids["B"]["chassis"],
        )
