# signals_list.py
import csv
import os
import ast
from harnice import fileio, component_library

# Signals list column headers to match source of truth + compatibility change
DEVICE_SIGNALS_HEADERS = [
    "channel_id",  # unique identifier for the channel
    "signal",
    "connector_name",
    "cavity",
    "connector_mpn",
    "channel_type",
    "compatible_channel_types",
]

DISCONNECT_SIGNALS_HEADERS = [
    "channel_id",  # unique identifier for the channel
    "signal",
    "A_cavity",
    "B_cavity",
    "A_connector_mpn",
    "A_channel_type",
    "A_compatible_channel_types",
    "B_connector_mpn",
    "B_channel_type",
    "B_compatible_channel_types",
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
        new_list()

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
            "A_channel_id",
            "A_signal",
            "A_connector_name",
            "A_cavity",
            "A_connector_mpn",
            "A_channel_type",
            "B_channel_id",
            "B_signal",
            "B_connector_name",
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

    # --- Handle compatibility fields ---
    if fileio.product_type == "device":
        channel_type = kwargs.get("channel_type", "")
        compat_list = compatible_channel_types(channel_type)
        kwargs["compatible_channel_types"] = (
            ",".join(str(x) for x in compat_list)
            if isinstance(compat_list, list)
            else ""
        )

    elif fileio.product_type == "disconnect":
        for prefix in ("A_", "B_"):
            channel_type = kwargs.get(f"{prefix}channel_type", "")
            compat_list = compatible_channel_types(channel_type)
            kwargs[f"{prefix}compatible_channel_types"] = (
                ",".join(str(x) for x in compat_list)
                if isinstance(compat_list, list)
                else ""
            )

    # --- Fill row in header order ---
    row = [kwargs.get(col, "") for col in headers]

    # --- Append to the signals list ---
    with open(signals_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter="\t", lineterminator="\n")
        writer.writerow(row)


# search channel_types.tsv
def signals_of_channel_type(channel_type):
    chid, lib_repo = parse_channel_type(channel_type)
    tsv_path = path_of_channel_type((chid, lib_repo))

    with open(tsv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            if str(row.get("channel_type", "")).strip() == str(chid):
                return [
                    sig.strip()
                    for sig in row.get("signals", "").split(",")
                    if sig.strip()
                ]
    return []


# search a known imported device's signals list
def signals_of_channel(channel_id, device_refdes):
    signals_list_path = os.path.join(
        fileio.dirpath("devices"), device_refdes, f"{device_refdes}-signals_list.tsv"
    )

    signals = []
    with open(signals_list_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            if row.get("channel_id", "").strip() == channel_id.strip():
                signals.append(row.get("signal", "").strip())
    return signals


def compatible_channel_types(channel_type):
    """
    Look up compatible channel_types for the given channel_type.
    Splits the TSV field by commas and parses each entry into (chid, lib_repo).
    """
    chid, lib_repo = parse_channel_type(channel_type)
    tsv_path = path_of_channel_type((chid, lib_repo))

    with open(tsv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            if str(chid) != str(row.get("channel_type")):
                continue

            signals_str = row.get("compatible_channel_types", "").strip()
            if not signals_str:
                return []

            values = [v.strip() for v in signals_str.split(";") if v.strip()]
            parsed = []
            for v in values:
                parsed.append(parse_channel_type(v))
            return parsed

    return []


def cavity_of_signal(channel_id, signal, path_to_signals_list):
    with open(path_to_signals_list, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
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


def path_of_channel_type(channel_type):
    """
    Args:
        channel_type: tuple like (chid, lib_repo) or string like "(5, '...')"
    """
    chid, lib_repo = parse_channel_type(channel_type)
    base_dir = component_library.get_local_path(lib_repo)
    return os.path.join(base_dir, "channel_types", "channel_types.tsv")


def parse_channel_type(val):
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
        channel_type = parse_channel_type(signal.get("channel_type"))
        expected_signals = signals_of_channel_type(channel_type)
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
        A_channel_type = parse_channel_type(signal.get("A_channel_type"))
        B_channel_type = parse_channel_type(signal.get("B_channel_type"))

        if B_channel_type not in compatible_channel_types(A_channel_type):
            if A_channel_type not in compatible_channel_types(B_channel_type):
                raise ValueError("A and B channel types are not compatible")

        expected_signals = signals_of_channel_type(A_channel_type)
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

    print(f"Signals list of {fileio.partnumber('pn')} is valid.\n")
