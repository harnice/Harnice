# signals_list.py
import csv
import os
import ast
from harnice import fileio, component_library

# Signals list column headers to match source of truth + compatibility change
DEVICE_SIGNALS_HEADERS = [
    "channel",
    "signal",
    "connector_name",
    "cavity",
    "connector_mpn",
    "channel_type_id",
    "compatible_channel_type_ids",
]

DISCONNECT_SIGNALS_HEADERS = [
    "channel",
    "signal",
    "A_cavity",
    "B_cavity",
    "A_connector_mpn",
    "A_channel_type_id",
    "A_compatible_channel_type_ids",
    "B_connector_mpn",
    "B_channel_type_id",
    "B_compatible_channel_type_ids",
]

global headers


def new_list(headers_arg):
    global headers
    if headers_arg == "device":
        headers = DEVICE_SIGNALS_HEADERS
    elif headers_arg == "disconnect":
        headers = DISCONNECT_SIGNALS_HEADERS

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


def read_list():
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
        new_list()

    # If channel_type_id is present, compute compatible_channel_type_ids
    if fileio.product_type == "device":
        channel_type_id = kwargs.get("channel_type_id", "")
        compat_list = compatible_channel_types(channel_type_id)

        # Join list into comma-separated string
        if isinstance(compat_list, list):
            kwargs["compatible_channel_type_ids"] = ",".join(
                str(x) for x in compat_list
            )
        else:
            kwargs["compatible_channel_type_ids"] = ""

    elif fileio.product_type == "disconnect":
        A_channel_type_id = kwargs.get("A_channel_type_id", "")
        B_channel_type_id = kwargs.get("B_channel_type_id", "")
        A_compat_list = compatible_channel_types(A_channel_type_id)
        B_compat_list = compatible_channel_types(B_channel_type_id)

        if isinstance(A_compat_list, list):
            kwargs["A_compatible_channel_type_ids"] = ",".join(
                str(x) for x in A_compat_list
            )
        else:
            kwargs["A_compatible_channel_type_ids"] = ""

        if isinstance(B_compat_list, list):
            kwargs["B_compatible_channel_type_ids"] = ",".join(
                str(x) for x in B_compat_list
            )
        else:
            kwargs["B_compatible_channel_type_ids"] = ""

    # Fill row according to headers
    row = [kwargs.get(col, "") for col in headers]

    with open(signals_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(row)


# search channel_types.tsv
def signals_of_channel_type_id(channel_type_id):
    chid, lib_repo = parse_channel_type_id(channel_type_id)
    tsv_path = path_of_channel_type_id((chid, lib_repo))

    with open(tsv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            if str(row.get("channel_type_id", "")).strip() == str(chid):
                return [
                    sig.strip()
                    for sig in row.get("signals", "").split(",")
                    if sig.strip()
                ]
    return []


# search a known imported device's signals list
def signals_of_channel(chname, device_refdes):
    signals_list_path = os.path.join(
        fileio.dirpath("devices"), device_refdes, f"{device_refdes}-signals_list.tsv"
    )

    signals = []
    with open(signals_list_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            if row.get("channel", "").strip() == chname.strip():
                signals.append(row.get("signal", "").strip())
    return signals


def compatible_channel_types(channel_type_id):
    """
    Look up compatible channel_type_ids for the given channel_type_id.
    Splits the TSV field by commas and parses each entry into (chid, lib_repo).
    """
    chid, lib_repo = parse_channel_type_id(channel_type_id)
    tsv_path = path_of_channel_type_id((chid, lib_repo))

    with open(tsv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            if str(chid) != str(row.get("channel_type_id")):
                continue

            signals_str = row.get("compatible_channel_type_ids", "").strip()
            if not signals_str:
                return []

            values = [v.strip() for v in signals_str.split(";") if v.strip()]
            parsed = []
            for v in values:
                parsed.append(parse_channel_type_id(v))
            return parsed

    return []


def cavity_of_signal(channel_id, signal, path_to_signals_list):
    with open(path_to_signals_list, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            if row.get("signal", "").strip() == signal.strip():
                if row.get("channel", "").strip() == channel_id.strip():
                    return row.get("cavity", "").strip()
        raise ValueError(f"Signal {signal} of channel {channel_id} not found in {path_to_signals_list}")


def connector_name_of_channel(channel_id, path_to_signals_list):
    if not os.path.exists(path_to_signals_list):
        raise FileNotFoundError(f"Signals list file not found: {path_to_signals_list}")

    with open(path_to_signals_list, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            if row.get("channel", "").strip() == channel_id.strip():
                return row.get("connector_name", "").strip()


def path_of_channel_type_id(channel_type_id):
    """
    Args:
        channel_type_id: tuple like (chid, lib_repo) or string like "(5, '...')"
    """
    chid, lib_repo = parse_channel_type_id(channel_type_id)
    base_dir = component_library.get_local_path(lib_repo)
    return os.path.join(base_dir, "channel_types", "channel_types.tsv")


def parse_channel_type_id(val):
    """Convert stored string into a tuple (chid:int, supplier:str)."""
    if not val:
        return None
    if isinstance(val, tuple):
        chid, supplier = val
    else:
        chid, supplier = ast.literal_eval(str(val))
    return (int(chid), str(supplier).strip())


def assert_unique(values, label):
    """Raise ValueError if duplicates are found in values."""
    seen = set()
    for v in values:
        if v in seen:
            raise ValueError(f"Duplicate {label} found: {v}")
        seen.add(v)


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
        channel_type_id = parse_channel_type_id(signal.get("channel_type_id"))
        expected_signals = signals_of_channel_type_id(channel_type_id)
        found_signals = set()
        connector_names = set()

        for expected_signal in expected_signals:
            for signal2 in signals_list:
                if (
                    signal2.get("channel") == signal.get("channel")
                    and signal2.get("signal") == expected_signal
                ):
                    found_signals.add(expected_signal)
                    connector_names.add(signal2.get("connector_name"))

        missing_signals = set(expected_signals) - found_signals
        if missing_signals:
            raise ValueError(
                f"Channel {signal.get('channel')} is missing signals: {', '.join(missing_signals)}"
            )

        if len(connector_names) > 1:
            raise ValueError(
                f"Channel {signal.get('channel')} has signals spread across multiple connectors: "
                f"{', '.join(connector_names)}"
            )

        counter += 1

    seen_contacts = set()
    for signal in signals_list:
        contact_key = f"{signal.get('connector_name')}-{signal.get('contact')}"
        if contact_key in seen_contacts:
            raise ValueError(
                f"Duplicate connector contact found in device: {contact_key}"
            )
        seen_contacts.add(contact_key)

    print(f"Signals list of {fileio.partnumber('pn')} is valid.\n")


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
        A_channel_type_id = parse_channel_type_id(signal.get("A_channel_type_id"))
        B_channel_type_id = parse_channel_type_id(signal.get("B_channel_type_id"))

        if B_channel_type_id not in compatible_channel_types(A_channel_type_id):
            if A_channel_type_id not in compatible_channel_types(B_channel_type_id):
                raise ValueError("A and B channel types are not compatible")

        expected_signals = signals_of_channel_type_id(A_channel_type_id)
        found_signals = set()

        for expected_signal in expected_signals:
            for signal2 in signals_list:
                if (
                    signal2.get("channel") == signal.get("channel")
                    and signal2.get("signal") == expected_signal
                ):
                    found_signals.add(expected_signal)

        missing_signals = set(expected_signals) - found_signals
        if missing_signals:
            raise ValueError(
                f"Channel {signal.get('channel')} is missing signals: {', '.join(missing_signals)}"
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

    print(f"Signals list of {fileio.partnumber('pn')} is valid.\n")
