from harnice import fileio, component_library, mapped_channels, fileio
import os
import csv
import ast

CHANNEL_MAP_COLUMNS = [
    "merged_net",
    "channel_type_id",
    "compatible_channel_type_ids",
    "from_device_refdes",
    "from_device_channel_id",
    "to_device_refdes",
    "to_device_channel_id",
    "multi_ch_junction_id",
    "disconnect_refdes_key",
]

NETLIST_COLUMNS = ["device_refdes", "net", "merged_net", "disconnect"]


def read_bom_rows():
    with open(fileio.path("bom"), "r", encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def pull_devices_from_library():
    imported_devices = []
    for refdes in read_bom_rows():
        if refdes.get("lib_repo") in ["", None]:
            os.makedirs(
                os.path.join(fileio.dirpath("devices"), refdes["device_ref_des"]),
                exist_ok=True,
            )
            continue

        if refdes not in imported_devices:
            if refdes.get("lib_repo") == "local":
                continue

            else:
                component_library.pull_item_from_library(
                    lib_repo=refdes["lib_repo"],
                    product="devices",
                    lib_subpath=refdes["lib_subpath"],
                    mpn=refdes["MPN"],
                    destination_directory=os.path.join(
                        fileio.dirpath("devices"), refdes["device_ref_des"]
                    ),
                    used_rev=None,
                    item_name=refdes["device_ref_des"],
                    quiet=False,
                )
        imported_devices.append(refdes)

def map_and_record(from_key, to_key):
    map_channel(from_key, to_key)
    mapped_channels.append(from_key)
    mapped_channels.append(to_key)


def read_signals_list(path):
    with open(path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def read_connector_list():
    connector_list = {}
    with open(fileio.path("system connector list"), "r", encoding="utf-8") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            merged_net = row.get("merged_net", "").strip()
            if not merged_net:
                continue
            entry = {
                "device_refdes": row.get("device_refdes", "").strip(),
                "net": row.get("net", "").strip(),
                "disconnect": row.get("disconnect", "").strip(),
            }
            connector_list.setdefault(merged_net, []).append(entry)
    return connector_list


def new_blank_channel_map():
    channel_map = []

    # load BOM
    with open(fileio.path("bom"), newline="", encoding="utf-8") as f:
        bom = list(csv.DictReader(f, delimiter="\t"))

    # load connector list
    with open(fileio.path("system connector list"), newline="", encoding="utf-8") as f:
        connector_list = list(csv.DictReader(f, delimiter="\t"))

    for connector in connector_list:
        device_refdes = connector.get("device_refdes")

        # look up mpn-rev from BOM
        device_mpn_rev = ""
        for item in bom:
            if item.get("device_ref_des") == device_refdes:
                device_mpn_rev = f"{item.get('MPN')}-{item.get('rev')}"
                break

        # signals list path
        if connector.get("disconnect"):
            # don't want disconnects to show up in channel map
            continue
        else:
            device_signals_list_path = os.path.join(
                fileio.dirpath("devices"),
                device_refdes,
                f"{device_mpn_rev}-signals_list.tsv",
            )

        # load signals list
        with open(device_signals_list_path, newline="", encoding="utf-8") as f:
            signals = list(csv.DictReader(f, delimiter="\t"))

        for signal in signals:
            sig_channel = signal.get("channel")

            # check if this channel is already in channel_map
            already = any(
                row.get("from_device_refdes") == device_refdes
                and row.get("from_device_channel_id") == sig_channel
                for row in channel_map
            )
            if already:
                continue

            # only concerned with signals on connectors from the connector list
            if not signal.get("connector_name") == connector.get("connector"):
                continue

            # build row
            channel_map_row = {
                "merged_net": connector.get("merged_net", ""),
                "channel_type_id": signal.get("channel_type_id", ""),
                "compatible_channel_type_ids": signal.get(
                    "compatible_channel_type_ids", ""
                ),
                "from_device_refdes": device_refdes,
                "from_device_channel_id": sig_channel,
                "to_device_refdes": "",
                "to_device_channel_id": "",
                "multi_ch_junction_id": "",
                "disconnect_refdes_key": "",
            }
            channel_map.append(channel_map_row)

    # write channel map TSV
    with open(fileio.path("channel map"), "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CHANNEL_MAP_COLUMNS, delimiter="\t")
        writer.writeheader()
        writer.writerows(channel_map)

    return channel_map


def read_channel_map():
    with open(fileio.path("channel map"), "r", encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def map_channel(from_key, to_key=None, multi_ch_junction_key=""):
    from_device_refdes, from_device_channel_id = from_key
    to_device_refdes, to_device_channel_id = to_key or (None, None)

    if not os.path.exists(fileio.path("channel map")):
        raise FileNotFoundError(
            f"Channel map not found at {fileio.path('channel map')}"
        )

    channels = read_channel_map()
    updated_channels, found_from, found_to = [], False, False
    require_to = bool(to_device_refdes or to_device_channel_id)

    for channel in channels:
        if (
            channel.get("from_device_refdes") == from_device_refdes
            and channel.get("from_device_channel_id") == from_device_channel_id
        ):
            channel["to_device_refdes"] = to_device_refdes or ""
            channel["to_device_channel_id"] = to_device_channel_id or ""
            if multi_ch_junction_key:
                channel["multi_ch_junction_id"] = multi_ch_junction_key
            found_from = True
        elif (
            require_to
            and channel.get("from_device_refdes") == to_device_refdes
            and channel.get("from_device_channel_id") == to_device_channel_id
        ):
            found_to = True
            continue #do not map to channel
        updated_channels.append(channel)

    if not found_from:
        raise ValueError(f"from_key {from_key} not found in channel map")
    if require_to and not found_to:
        raise ValueError(f"to_key {to_key} not found in channel map")

    with open(fileio.path("channel map"), "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CHANNEL_MAP_COLUMNS, delimiter="\t")
        writer.writeheader()
        writer.writerows(updated_channels)


def compatible_channel_type_ids(from_key):
    refdes, ch_id = from_key
    for row in read_channel_map():
        if (
            row.get("from_device_refdes") == refdes
            and row.get("from_device_channel_id") == ch_id
        ):
            raw_val = row.get("compatible_channel_type_ids", "")
            if not raw_val:
                return []
            try:
                parsed = ast.literal_eval(raw_val)
                return parsed if isinstance(parsed, list) else [parsed]
            except Exception:
                return [t.strip() for t in str(raw_val).split(",") if t.strip()]
    return []


def mpn_of_device_refdes(refdes):
    for row in read_bom_rows():
        if row.get("device_ref_des") == refdes:
            return row.get("MFG"), row.get("MPN"), row.get("rev")
    return None, None, None
