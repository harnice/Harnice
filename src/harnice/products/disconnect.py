import runpy
import os
import csv
from harnice import fileio, state
from harnice.products import chtype

disconnect_feature_tree_utils_default = """
from harnice.lists import signals_list

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
        signals_list.append(
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
        signals_list.append(
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


def file_structure():
    return {
        f"{state.partnumber('pn-rev')}-feature_tree.py": "feature tree",
        f"{state.partnumber('pn-rev')}-signals_list.tsv": "signals list",
        f"{state.partnumber('pn-rev')}-attributes.json": "attributes",
    }


def generate_structure():
    pass


# TODO-448 i don't think users should be calling this
def _validate_signals_list():
    print("--------------------------------")
    print("Validating signals list...")
    if not os.path.exists(fileio.path("signals list")):
        raise FileNotFoundError("Signals list was not generated.")

    with open(fileio.path("signals list"), "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        headers = reader.fieldnames
        signals_list = list(reader)

    if not headers:
        raise ValueError("Signals list has no header row.")

    counter = 2
    for signal in signals_list:
        print("Looking at csv row:", counter)
        A_channel_type = chtype.parse(signal.get("A_channel_type"))
        B_channel_type = chtype.parse(signal.get("B_channel_type"))

        # make sure all the fields are there
        if signal.get("channel_id") in ["", None]:
            raise ValueError("A_channel_id is blank")
        if signal.get("signal") in ["", None]:
            raise ValueError("signal is blank")
        if signal.get("A_cavity") in ["", None]:
            raise ValueError("A_cavity is blank")
        if signal.get("B_cavity") in ["", None]:
            raise ValueError("B_cavity is blank")
        if signal.get("A_connector_mpn") in ["", None]:
            raise ValueError("A_connector_mpn is blank")
        if signal.get("A_channel_type") in ["", None]:
            raise ValueError("A_channel_type is blank")
        if signal.get("B_connector_mpn") in ["", None]:
            raise ValueError("B_connector_mpn is blank")
        if signal.get("B_channel_type") in ["", None]:
            raise ValueError("B_channel_type is blank")

        # make sure signal is a valid signal of its channel type
        if signal.get("signal") not in chtype.signals(A_channel_type):
            raise ValueError(
                f"Signal {signal.get('A_signal')} is not a valid signal of its channel type"
            )

        # make sure A and B sides are compatible
        if B_channel_type not in chtype.compatibles(A_channel_type):
            if A_channel_type not in chtype.compatibles(B_channel_type):
                raise ValueError("A and B channel types are not compatible")

        expected_signals = chtype.signals(A_channel_type)
        found_signals = set()

        # make sure all the signals of each channel type are present
        for expected_signal in expected_signals:
            for signal2 in signals_list:
                if (
                    signal2.get("channel_id") == signal.get("channel_id")
                    and signal2.get("signal") == expected_signal
                ):
                    found_signals.add(expected_signal)

        missing_signals = set(expected_signals) - found_signals
        if missing_signals:
            raise ValueError(
                f"Channel {signal.get('channel_id')} is missing signals: {', '.join(missing_signals)}"
            )

        counter += 1

    # make sure no duplicate A-side cavities are present
    seen_A = set()
    for signal in signals_list:
        A_cavity = signal.get("A_cavity")
        if A_cavity in seen_A:
            raise ValueError(f"Duplicate A_cavity found in disconnect: {A_cavity}")
        seen_A.add(A_cavity)

    # make sure no duplicate B-side cavities are present
    seen_B = set()
    for signal in signals_list:
        B_cavity = signal.get("B_cavity")
        if B_cavity in seen_B:
            raise ValueError(f"Duplicate B_cavity found in disconnect: {B_cavity}")
        seen_B.add(B_cavity)

    if counter == 2:
        raise ValueError(
            "No signals have been specified. Check your feature tree or add rows manually."
        )

    print(f"Signals list of {state.partnumber('pn')} is valid.\n")


def render():
    fileio.set_file_structure(file_structure())
    fileio.verify_revision_structure(product_type="device")  # identical for now
    generate_structure()

    if not os.path.exists(fileio.path("signals list")):
        if not os.path.exists(fileio.path("feature tree")):
            with open(fileio.path("feature tree"), "w", encoding="utf-8") as f:
                f.write(disconnect_feature_tree_utils_default)

    if os.path.exists(fileio.path("feature tree")):
        runpy.run_path(fileio.path("feature tree"))
        print("Successfully rebuilt signals list per feature tree.")

    _validate_signals_list()
