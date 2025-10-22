import runpy
import os
from harnice import fileio, signals_list

disconnect_feature_tree_default = """
from harnice import signals_list

ch_type_ids = {
    "A": {
        "balanced audio mic level in": (1, "https://github.com/kenyonshutt/harnice-library-public"),
        "chassis": (5, "https://github.com/kenyonshutt/harnice-library-public")
    },
    "B": {
        "balanced audio mic level out": (2, "https://github.com/kenyonshutt/harnice-library-public"),
        "chassis": (5, "https://github.com/kenyonshutt/harnice-library-public")
    }
}

cn_mpns = {
    "A": "DB25F",
    "B": "DB25M"
}

cavity_number = {
    "ch0": {
        "pos": 24,
        "neg": 12,
        "chassis": 25
    },
    "ch1": {
        "pos": 10,
        "neg": 23,
        "chassis": 11
    },
    "ch2": {
        "pos": 21,
        "neg": 9,
        "chassis": 22
    },
    "ch3": {
        "pos": 7,
        "neg": 20,
        "chassis": 8
    },
    "ch4": {
        "pos": 18,
        "neg": 6,
        "chassis": 19
    },
    "ch5": {
        "pos": 4,
        "neg": 17,
        "chassis": 5
    },
    "ch6": {
        "pos": 15,
        "neg": 3,
        "chassis": 16
    },
    "ch7": {
        "pos": 1,
        "neg": 14,
        "chassis": 2
    },
}

signals_list.new()

for channel in range(8):
    channel_name = f"ch{channel}"

    for signal in signals_list.signals_of_channel_type(ch_type_ids["A"]["balanced audio mic level in"]):
        signals_list.write_signal(
            channel=channel_name,
            signal=signal,

            A_cavity=cavity_number[channel_name][signal],
            A_connector_mpn=cn_mpns["A"],
            A_channel_type=ch_type_ids["A"]["balanced audio mic level in"],

            B_cavity=cavity_number[channel_name][signal],
            B_connector_mpn=cn_mpns["B"],
            B_channel_type=ch_type_ids["B"]["balanced audio mic level out"],
        )

    for signal in signals_list.signals_of_channel_type(ch_type_ids["A"]["chassis"]):
        signals_list.write_signal(
            channel=f"{channel_name}-shield",
            signal=signal,

            A_cavity=cavity_number[channel_name][signal],
            A_connector_mpn=cn_mpns["A"],
            A_channel_type=ch_type_ids["A"]["chassis"],

            B_cavity=cavity_number[channel_name][signal],
            B_connector_mpn=cn_mpns["B"],
            B_channel_type=ch_type_ids["B"]["chassis"],
        )

"""


def render():
    fileio.verify_revision_structure(product_type="device")  # identical for now

    if not os.path.exists(fileio.path("signals list")):
        if not os.path.exists(fileio.path("feature tree")):
            with open(fileio.path("feature tree"), "w", encoding="utf-8") as f:
                f.write(disconnect_feature_tree_default)

    if os.path.exists(fileio.path("feature tree")):
        runpy.run_path(fileio.path("feature tree"))
        print("Successfully rebuilt signals list per feature tree.")

    signals_list.validate_for_disconnect()
