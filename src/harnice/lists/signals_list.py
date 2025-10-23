# signals_list.py
import csv
import os
from harnice import fileio
from harnice.products import chtype

# Signals list column headers to match source of truth + compatibility change
DEVICE_COLUMNS = [
    "channel_id",  # unique identifier for the channel
    "signal",
    "connector_name",
    "cavity",
    "connector_mpn",
    "channel_type",
]

DISCONNECT_COLUMNS = [
    "channel_id",  # unique identifier for the channel
    "signal",
    "A_cavity",
    "B_cavity",
    "A_connector_mpn",
    "A_channel_type",
    "B_connector_mpn",
    "B_channel_type",
]

global headers


def new():
    global headers
    if fileio.product_type == "device":
        headers = DEVICE_COLUMNS
    elif fileio.product_type == "disconnect":
        headers = DISCONNECT_COLUMNS

    """
    Creates a new signals TSV file at fileio.path("signals list") with only the header row.
    Overwrites any existing file.
    """
    signals_path = fileio.path("signals list")
    os.makedirs(os.path.dirname(signals_path), exist_ok=True)

    if os.path.exists(signals_path):
        os.remove(signals_path)

    with open(signals_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(headers)


def append(**kwargs):
    """
    Appends a new row to the signals TSV file.
    Missing optional fields will be written as empty strings.
    Raises ValueError if required fields are missing.

    Required kwargs:
        For 'device':
            channel_id, signal, connector_name, cavity, connector_mpn, channel_type
        For 'disconnect':
            A_channel_id, A_signal, A_connector_name, A_cavity, A_connector_mpn, A_channel_type,
            B_channel_id, B_signal, B_connector_name, B_cavity, B_connector_mpn, B_channel_type
    """
    signals_path = fileio.path("signals list")

    # Create the signals list file if it doesn't exist
    if not os.path.exists(signals_path):
        new()

    # --- Define required fields based on product type ---
    if fileio.product_type == "device":
        required = [
            "channel_id",
            "signal",
            "connector_name",
            "cavity",
            "connector_mpn",
            "channel_type",
        ]
    elif fileio.product_type == "disconnect":
        required = [
            "channel_id",
            "signal",
            "A_cavity",
            "A_connector_mpn",
            "A_channel_type",
            "B_cavity",
            "B_connector_mpn",
            "B_channel_type",
        ]
    else:
        required = []

    # --- Check for missing required fields ---
    missing = [key for key in required if not kwargs.get(key)]
    if missing:
        raise ValueError(
            f"Missing required signal fields for {fileio.product_type}: {', '.join(missing)}"
        )

    # --- Fill row in header order ---
    row = [kwargs.get(col, "") for col in headers]

    # --- Append to the signals list ---
    with open(signals_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter="\t", lineterminator="\n")
        writer.writerow(row)


def cavity_of_signal(channel_id, signal, path_to_signals_list):
    for row in fileio.read_tsv(path_to_signals_list):
        if row.get("signal", "").strip() == signal.strip():
            if row.get("channel_id", "").strip() == channel_id.strip():
                return row.get("cavity", "").strip()
    raise ValueError(
        f"Signal {signal} of channel_id {channel_id} not found in {path_to_signals_list}"
    )


def connector_name_of_channel(channel_id, path_to_signals_list):
    if not os.path.exists(path_to_signals_list):
        raise FileNotFoundError(f"Signals list file not found: {path_to_signals_list}")

    with open(path_to_signals_list, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            if row.get("channel_id", "").strip() == channel_id.strip():
                return row.get("connector_name", "").strip()


# TODO-448 i don't think users should be calling this
def validate_for_device():
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
        channel_type = chtype.parse(signal.get("channel_type"))
        expected_signals = chtype.signals(channel_type)
        found_signals = set()
        connector_names = set()

        for expected_signal in expected_signals:
            for signal2 in signals_list:
                if (
                    signal2.get("channel_id") == signal.get("channel_id")
                    and signal2.get("signal") == expected_signal
                ):
                    found_signals.add(expected_signal)
                    connector_names.add(signal2.get("connector_name"))

        missing_signals = set(expected_signals) - found_signals
        if missing_signals:
            raise ValueError(
                f"Channel {signal.get('channel_id')} is missing signals: {', '.join(missing_signals)}"
            )

        if len(connector_names) > 1:
            raise ValueError(
                f"Channel {signal.get('channel_id')} has signals spread across multiple connectors: "
                f"{', '.join(connector_names)}"
            )

        counter += 1

    seen_cavities = set()
    for signal in signals_list:
        cavity_key = f"{signal.get('connector_name')}-{signal.get('cavity')}"
        if cavity_key in seen_cavities:
            raise ValueError(
                f"Duplicate cavity '{signal.get('cavity')}' found on connector '{signal.get('connector_name')}'"
            )
        seen_cavities.add(cavity_key)

    print(f"Signals list of {fileio.partnumber('pn')} is valid.\n")


# TODO-448 i don't think users should be calling this
def validate_for_disconnect():
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

        if B_channel_type not in chtype.compatibles(A_channel_type):
            if A_channel_type not in chtype.compatibles(B_channel_type):
                raise ValueError("A and B channel types are not compatible")

        expected_signals = chtype.signals(A_channel_type)
        found_signals = set()

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

    seen_A = set()
    for signal in signals_list:
        A_cavity = signal.get("A_cavity")
        if A_cavity in seen_A:
            raise ValueError(f"Duplicate A_cavity found in disconnect: {A_cavity}")
        seen_A.add(A_cavity)

    # Check duplicates for B side
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

    print(f"Signals list of {fileio.partnumber('pn')} is valid.\n")
