import csv
import os
from harnice import fileio

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
