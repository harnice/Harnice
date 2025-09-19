# icd.py
import csv
import os
from harnice import fileio, component_library

# Signals list column headers to match source of truth + compatibility change
SIGNALS_HEADERS = [
    "channel",
    "signal",
    "connector_name",
    "contact",
    "connector_mpn",
    "channel_type_id",
    "channel_type_id_status",
    "channel_type_id_description",
    "compatible_channel_type_ids",
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

def read_signals_list():
    signals_path = fileio.path("signals list")
    with open(signals_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        return list(reader)

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

#search channel_types.tsv
def signals_of_channel_type_id(channel_type_id):
    chid, supplier = component_library.unpack_channel_type_id(channel_type_id)

    tsv_path = _channel_types_path((chid, supplier))

    with open(tsv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            if str(row.get("channel_type_id", "")).strip() == str(chid):
                signals_str = row.get("signals", "")
                return [sig.strip() for sig in signals_str.split(",") if sig.strip()]
    return []

#search a known imported device's signals list
def signals_of_channel(channel_name, path_to_signals_list):
    if not os.path.exists(path_to_signals_list):
        return ""

    signals = []
    
    with open(path_to_signals_list, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            if row.get("channel", "").strip() == channel_name.strip():
                signals.append(row.get("signal", "").strip())
    return signals

def compatible_channel_types(channel_type_id, ch_type_id_supplier="https://github.com/kenyonshutt/harnice-library-public"):
    tsv_path = _channel_types_path(ch_type_id_supplier)

    with open(tsv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            if str(row.get("compatible_channel_type_ids", "")).strip() == str(channel_type_id):
                signals_str = row.get("signals", "")
                return [sig.strip() for sig in signals_str.split(",") if sig.strip()]
    return []

def pin_of_signal(signal, path_to_signals_list):
    """
    Returns the pin/contact information for a given signal from the signals list.
    
    Args:
        signal (str): The signal name to search for
        path_to_signals_list (str): Path to the signals list TSV file
        
    Returns:
        str: The pin/contact information for the signal, or empty string if not found
    """
    if not os.path.exists(path_to_signals_list):
        return ""
    
    with open(path_to_signals_list, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            if row.get("signal", "").strip() == signal.strip():
                return row.get("contact", "").strip()
    return ""

def mating_connector_of_channel(channel_id, path_to_signals_list):
    if not os.path.exists(path_to_signals_list):
        raise FileNotFoundError(f"Signals list file not found: {path_to_signals_list}")
    
    with open(path_to_signals_list, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            if row.get("channel", "").strip() == channel_id.strip():
                return row.get("connector_name", "").strip()

def _channel_types_path(channel_type_id):
    """
    Helper to get the path to channel_types.tsv.

    Args:
        channel_type_id: tuple like (chid, supplier) or string like "(5, 'https://github.com/kenyonshutt/harnice-library-public')"
    """
    chid, supplier = component_library.unpack_channel_type_id(channel_type_id)  # <-- use your helper

    base_dir = component_library.get_local_path(supplier)

    tsv_path = os.path.join(base_dir, "channel_types", "channel_types.tsv")

    return os.path.expanduser(tsv_path)  # <-- expand ~ to full home dir
