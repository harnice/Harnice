from harnice import fileio, component_library, mapped_channels
import os
import csv
import json

CHANNEL_MAP_COLUMNS = [
    "merged_net",
    "channel_type_id",
    "compatible_channel_type_ids",
    "from_device_refdes",
    "from_device_channel_id",
    "to_device_refdes",
    "to_device_channel_id",
    "multi_ch_junction_id",
]


def read_bom_rows():
    with open(fileio.path("bom"), "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        return list(reader)


def pull_devices_from_library():
    imported_devices = []

    for refdes in read_bom_rows():
        if refdes["lib_repo"] in ["", None]:
            os.makedirs(os.path.join(fileio.dirpath("devices"), refdes["device_ref_des"]), exist_ok=True)
            continue

        if refdes not in imported_devices:
            # import device from library

            component_library.pull_item_from_library(
                lib_repo=refdes["lib_repo"],
                lib_subpath="devices/" + refdes["lib_subpath"],
                mpn=refdes["MPN"],
                destination_directory=os.path.join(
                    fileio.dirpath("devices"), refdes["device_ref_des"]
                ),
                used_rev=None,
                item_name=refdes["device_ref_des"],
                quiet=False,
            )
        imported_devices.append(refdes)


def read_signals_list(path):
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        return list(reader)


def read_netlist():
    with open(fileio.path("netlist"), "r", encoding="utf-8") as f:
        return json.load(f)


def new_blank_channel_map():
    with open(fileio.path("channel map"), "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CHANNEL_MAP_COLUMNS, delimiter="\t")
        writer.writeheader()
        writer.writerows([])

    channel_map = []
    seen = set()  # track unique rows by tuple key
    netlist = read_netlist()  # load once

    for refdes in read_bom_rows():
        device_ref = refdes.get("device_ref_des")
        if not device_ref:
            continue

        signals_path = os.path.join(
            fileio.dirpath("devices"),
            device_ref,
            f"{refdes.get('MPN')}-{refdes.get('rev')}-signals-list.tsv",
        )
        if not os.path.exists(signals_path):
            continue

        signals = read_signals_list(signals_path)
        if not signals:
            continue

        for signal in signals:
            channel_id = signal.get("channel", "").strip()
            if not channel_id:
                continue

            connector_name_of_channel = (
                f"{device_ref}:{signal.get('connector_name', '').strip()}"
            )
            merged_net = next(
                (
                    net
                    for net, conns in netlist.items()
                    if connector_name_of_channel in conns
                ),
                None,
            )

            row = {
                "merged_net": merged_net,
                "channel_type_id": signal.get("channel_type_id", "").strip(),
                "compatible_channel_type_ids": signal.get(
                    "compatible_channel_type_ids", ""
                ).strip(),
                "from_device_refdes": device_ref,
                "from_device_channel_id": channel_id,
            }

            # create a uniqueness key from row values
            key = (
                row["merged_net"],
                row["from_device_refdes"],
                row["from_device_channel_id"],
            )

            if key not in seen:
                channel_map.append(row)
                seen.add(key)

    with open(fileio.path("channel map"), "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CHANNEL_MAP_COLUMNS, delimiter="\t")
        writer.writeheader()
        writer.writerows(channel_map)

    mapped_channels.new_set()


def read_channel_map():
    with open(fileio.path("channel map"), "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        return list(reader)


def map_channel(from_key, to_key=None, multi_ch_junction_key=""):
    """
    Updates the channel map:
    1. Finds the row with from_key (tuple: (refdes, channel_id)) and updates its 'to' fields.
    2. Removes the row with to_key (tuple: (refdes, channel_id)), unless to_key is [None, None].
    3. Optionally adds multi_ch_junction_key to the from row.

    Args:
        from_key: [refdes, channel_id] (required)
        to_key: [refdes, channel_id] or [None, None] (default: [None, None])
        multi_ch_junction_key: optional junction ID

    Raises:
        ValueError if from_key is not found in the channel map.
        ValueError if non-empty to_key is not found in the channel map.
    """
    from_device_refdes, from_device_channel_id = from_key
    if to_key is None:
        to_key = [None, None]
    to_device_refdes, to_device_channel_id = to_key

    path = fileio.path("channel map")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Channel map not found at {path}")

    updated_rows = []
    found_from = False
    found_to = False
    require_to = bool(
        to_device_refdes or to_device_channel_id
    )  # only enforce if non-empty

    # Load all rows once
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        fieldnames = reader.fieldnames
        rows = list(reader)

    for row in rows:
        if (
            row.get("from_device_refdes") == from_device_refdes
            and row.get("from_device_channel_id") == from_device_channel_id
        ):
            # Update FROM row
            row["to_device_refdes"] = to_device_refdes or ""
            row["to_device_channel_id"] = to_device_channel_id or ""
            if multi_ch_junction_key:
                row["multi_ch_junction_id"] = multi_ch_junction_key
            found_from = True
            updated_rows.append(row)
            continue

        if (
            require_to
            and row.get("from_device_refdes") == to_device_refdes
            and row.get("from_device_channel_id") == to_device_channel_id
        ):
            # Drop TO row entirely
            found_to = True
            continue

        updated_rows.append(row)

    # Explicit error checks
    if not found_from:
        raise ValueError(f"from_key {from_key} not found in channel map")
    if require_to and not found_to:
        raise ValueError(f"to_key {to_key} not found in channel map")

    # Write back
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        writer.writerows(updated_rows)


def compatible_channel_type_ids(from_key):
    """
    Given a (from_device_refdes, from_device_channel_id) tuple,
    return a list of compatible channel_type_ids.
    """
    refdes, ch_id = from_key
    for row in read_channel_map():
        if (
            row.get("from_device_refdes") == refdes
            and row.get("from_device_channel_id") == ch_id
        ):
            return [
                t.strip()
                for t in str(row.get("compatible_channel_type_ids", "")).split(",")
                if t.strip()
            ]
    return []


def mpn_of_device_refdes(refdes):
    for row in read_bom_rows():
        if row.get("device_ref_des") == refdes:
            return row.get("MFG"), row.get("MPN"), row.get("rev")
    return None, None, None
