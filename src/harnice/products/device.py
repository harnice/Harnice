import os
import runpy
import csv
from harnice import fileio, icd

signals_list_feature_tree_default = """
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
            signal=signal,
            connector_name=connector_name,
            contact=xlr_pinout.get(signal)
            channel_type_id=channel_type_id,
            channel_type_id_supplier="public",
            connector_mpn=connector_mpn
        )

    # Add shield row
    icd.write_signal(
        channel=f"{channel_name}-shield",
        signal="shield",
        connector_name=connector_name,
        contact=xlr_pinout.get("shield")
        channel_type_id=ch_type_ids["shield"],
        channel_type_id_supplier="public",
        connector_mpn=connector_mpn
    )

"""

def render():
    fileio.verify_revision_structure()

    # Create signals list feature tree file if no list.
    if not os.path.exists(fileio.path("signals list")):
        with open(fileio.path("feature tree"), "w", encoding="utf-8") as f:
            f.write(signals_list_feature_tree_default)

    # Run the signals list feature tree script
    if os.path.exists(fileio.path("feature tree")):
        runpy.run_path(fileio.path("feature tree"))
        print("Successfully rebuilt signals list per feature tree.")


################ Validate signals list

    # make sure signals list exists
    if not os.path.exists(fileio.path("signals list")):
        raise FileNotFoundError("Signals list was not generated.")

    # load the signals list to read it in subsequent checks
    signals_list = []
    with open(fileio.path("signals list"), "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        signals_list = list(reader)

    # make sure the required headers are present and in the correct order
    required_headers = icd.SIGNALS_HEADERS
    actual_headers = list(signals_list[0].keys())

    if actual_headers[:len(required_headers)] != required_headers:
        raise ValueError(
            f"Signals list headers are incorrect.\n"
            f"Expected: {required_headers}\n"
            f"Found:    {actual_headers[:len(required_headers)]}"
        )

    # make sure the required fields are present for each signal
    required_fields = ["channel", "signal", "connector_name", "channel_type_id", "compatible_channel_type_ids"]
    for signal in signals_list:
        for field in required_fields:
            if field not in signal:
                raise ValueError(f"Channel {signal.get('channel')} is missing the field: {field}")

    # make sure every signal of a channel is accounted for
    for signal in signals_list:
        channel_type_id, supplier = signal.get("channel_type_id").strip("[]").split(",")
        expected_signals_of_channel = icd.signals_of_channel_type_id(channel_type_id, supplier)

        found_signals = set()
        connector_names = set()

        for expected_signal in expected_signals_of_channel:
            for signal2 in signals_list:
                if (
                    signal2.get("channel") == signal.get("channel")
                    and signal2.get("signal") == expected_signal
                ):
                    found_signals.add(expected_signal)
                    connector_names.add(signal2.get("connector_name"))

        # --- Check completeness ---
        missing_signals = set(expected_signals_of_channel) - found_signals
        if missing_signals:
            raise ValueError(
                f"Channel {signal.get('channel')} is missing signals: {', '.join(missing_signals)}"
            )

        # --- Check connector consistency ---
        if len(connector_names) > 1:
            raise ValueError(
                f"Channel {signal.get('channel')} has signals spread across multiple connectors: "
                f"{', '.join(connector_names)}"
            )

    # make sure no connector contacts are duplicated
    seen_contacts = set()

    for signal in signals_list:
        contact_key = f"{signal.get('connector_name')}-{signal.get('contact')}"
        if contact_key in seen_contacts:
            raise ValueError(f"Duplicate connector contact found: {contact_key}")
        seen_contacts.add(contact_key)

    print(f"Signals list of {fileio.partnumber('pn')} is valid.\n")
