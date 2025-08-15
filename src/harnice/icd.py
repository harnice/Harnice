# icd.py
import csv
import os
from dotenv import load_dotenv
from harnice import fileio

# Signals list column headers to match source of truth + compatibility change
SIGNALS_HEADERS = [
    "channel",
    "channel_type_id",
    "compatible_channel_ids",
    "signal",
    "connector",
    "connector_mpn",
    "contact"
]

def new_signals_list():
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
        writer.writerow(SIGNALS_HEADERS)

def write_signal(**kwargs):
    """
    Appends a new row to the signals TSV file.
    Missing fields will be written as empty strings.
    """
    signals_path = fileio.path("signals list")

    if not os.path.exists(signals_path):
        new_signals_list()

    row = [kwargs.get(col, "") for col in SIGNALS_HEADERS]

    with open(signals_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(row)

def signals_of_channel_type(channel_type_name, channel_type_id, ch_type_id_supplier="public"):
    """
    Reads the channel_types.tsv file for the given channel_type_id and returns a list of signals.
    """
    load_dotenv()
    tsv_path = _channel_types_path(ch_type_id_supplier)

    with open(tsv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            if str(row.get("channel_type_id", "")).strip() == str(channel_type_id):
                signals_str = row.get("signals", "")
                return [sig.strip() for sig in signals_str.split(",") if sig.strip()]
    return []

def compatible_channels(channel_type_name, ch_type_ids, ch_type_id_supplier="public"):
    """
    Reads the 'compatible_channel_ids' column from channel_types.tsv for the given channel type.
    Returns as a comma-separated string of integers.
    """
    load_dotenv()
    channel_type_id = ch_type_ids.get(channel_type_name)
    if channel_type_id is None:
        return ""

    tsv_path = _channel_types_path(ch_type_id_supplier)

    with open(tsv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            if str(row.get("channel_type_id", "")).strip() == str(channel_type_id):
                comp_str = row.get("compatible_channel_ids", "")
                return ",".join([cid.strip() for cid in comp_str.split(",") if cid.strip()])
    return ""

def _channel_types_path(ch_type_id_supplier):
    """
    Helper to get the path to channel_types.tsv based on an environment variable.
    """
    base_dir = os.environ.get(ch_type_id_supplier)
    if not base_dir:
        raise EnvironmentError(f"Environment variable '{ch_type_id_supplier}' is not set.")
    tsv_path = os.path.join(base_dir, "channel_types", "channel_types.tsv")
    if not os.path.exists(tsv_path):
        raise FileNotFoundError(f"Channel types file not found: {tsv_path}")
    return tsv_path
