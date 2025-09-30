from harnice import fileio, component_library, mapped_channels
import os
import csv
import ast
from collections import deque


CHANNEL_MAP_COLUMNS = [
    "merged_net",
    "from_device_refdes",
    "from_device_channel_id",
    "from_channel_type_id",
    "from_compatible_channel_type_ids",
    "to_device_refdes",
    "to_device_channel_id",
    "to_channel_type_id",
    "to_compatible_channel_type_ids",
    "multi_ch_junction_id",
    "disconnect_refdes_key",
    "manual_map_channel_python_equiv",
]

DISCONNECT_CHANNEL_MAP_COLUMNS = [
    "merged_net",
    "channel_type_id",
    "compatible_channel_type_ids",
    "from_destination_device_refdes",
    "from_destination_device_channel_id",
    "to_destination_device_refdes",
    "to_destination_device_channel_id",
    "disconnect_refdes",
    "disconnect_channel_id",
]

NETLIST_COLUMNS = ["device_refdes", "net", "merged_net", "disconnect"]


def read_bom_rows():
    with open(fileio.path("bom"), "r", encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def pull_devices_from_library():
    imported_devices = []
    for refdes in read_bom_rows():
        if refdes not in imported_devices:
            if refdes.get("disconnect") == "TRUE":
                os.makedirs(
                    os.path.join(
                        fileio.dirpath("disconnects"), refdes["device_ref_des"]
                    ),
                    exist_ok=True,
                )
                if refdes.get("lib_repo") == "local":
                    continue
                if not refdes.get("MPN"):
                    raise ValueError(
                        f"MPN is required for disconnect refdes {refdes['device_ref_des']}"
                    )
                else:
                    component_library.pull_item_from_library(
                        lib_repo=refdes["lib_repo"],
                        product="disconnects",
                        lib_subpath=refdes["lib_subpath"],
                        mpn=refdes["MPN"],
                        destination_directory=os.path.join(
                            fileio.dirpath("disconnects"), refdes["device_ref_des"]
                        ),
                        used_rev=None,
                        item_name=refdes["device_ref_des"],
                        quiet=False,
                    )
                continue

            else:
                os.makedirs(
                    os.path.join(fileio.dirpath("devices"), refdes["device_ref_des"]),
                    exist_ok=True,
                )
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
        if connector.get("disconnect") == "TRUE":
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
                "from_channel_type_id": signal.get("channel_type_id", ""),
                "from_compatible_channel_type_ids": signal.get(
                    "compatible_channel_type_ids", ""
                ),
                "from_device_refdes": device_refdes,
                "from_device_channel_id": sig_channel,
            }
            channel_map.append(channel_map_row)

    # write channel map TSV
    with open(fileio.path("channel map"), "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CHANNEL_MAP_COLUMNS, delimiter="\t")
        writer.writeheader()
        writer.writerows(channel_map)

    return channel_map


def new_blank_disconnect_map():
    disconnect_channel_map = []

    # load channel map
    with open(fileio.path("channel map"), newline="", encoding="utf-8") as f:
        channel_map = list(csv.DictReader(f, delimiter="\t"))

    for channel in channel_map:
        disconnect_refdes_keys = []

        raw = channel.get("disconnect_refdes_key")
        if raw:
            # Case 1: already a Python list
            if isinstance(raw, list):
                disconnect_refdes_keys = raw
            else:
                # Case 2: string that looks like a list -> parse safely
                try:
                    parsed = ast.literal_eval(raw)
                    if isinstance(parsed, list):
                        disconnect_refdes_keys = parsed
                    else:
                        # fallback: strip brackets and split manually
                        clean = raw.replace("[", "").replace("]", "")
                        disconnect_refdes_keys = [x.strip() for x in clean.split(",") if x.strip()]
                except Exception:
                    # fallback: strip brackets and split manually
                    clean = raw.replace("[", "").replace("]", "")
                    disconnect_refdes_keys = [x.strip() for x in clean.split(",") if x.strip()]

        for disconnect_refdes_key in disconnect_refdes_keys:
            disconnect_channel_map.append(
                {
                    "merged_net": channel.get("merged_net"),
                    "channel_type_id": channel.get("channel_type_id"),
                    "compatible_channel_type_ids": channel.get("compatible_channel_type_ids"),
                    "from_destination_device_refdes": channel.get("from_device_refdes"),
                    "from_destination_device_channel_id": channel.get("from_device_channel_id"),
                    "to_destination_device_refdes": channel.get("to_device_refdes"),
                    "to_destination_device_channel_id": channel.get("to_device_channel_id"),
                    "disconnect_refdes": disconnect_refdes_key,
                }
            )

    with open(fileio.path("disconnect channel map"), "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=DISCONNECT_CHANNEL_MAP_COLUMNS, delimiter="\t")
        writer.writeheader()
        writer.writerows(disconnect_channel_map)


def read_channel_map():
    with open(fileio.path("channel map"), "r", encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def map_channel(from_key, to_key=None, multi_ch_junction_key=""):
    if not os.path.exists(fileio.path("channel map")):
        raise FileNotFoundError(
            f"Channel map not found at {fileio.path('channel map')}"
        )

    channels = read_channel_map()

    to_device_refdes, to_device_channel_id = to_key or (None, None)

    to_channel = None
    for channel in channels:
        if channel.get("from_device_refdes") == from_key[0] and channel.get("from_device_channel_id") == from_key[1]:
            to_channel = channel
            break

    if not to_channel:
        raise ValueError(f"to_key {to_key} not found in channel map")

    updated_channels, found_from, found_to = [], False, False
    require_to = bool(to_device_refdes or to_device_channel_id)

    for channel in channels:
        if (
            channel.get("from_device_refdes") == from_key[0]
            and channel.get("from_device_channel_id") == from_key[1]
        ):
            channel["to_device_refdes"] = to_channel.get("to_device_refdes")
            channel["to_device_channel_id"] = to_channel.get("to_device_channel_id")
            channel["to_channel_type_id"] = to_channel.get("to_channel_type_id")
            channel["to_compatible_channel_type_ids"] = to_channel.get("to_compatible_channel_type_ids")
            channel["to_device_channel_id"] = to_device_channel_id
            if multi_ch_junction_key:
                channel["multi_ch_junction_id"] = multi_ch_junction_key
            found_from = True
            # add python equivalent to channel map to help user grab this map and force its use here or elsewhere
            if require_to:
                channel["manual_map_channel_python_equiv"] = (
                    f"system_utils.map_and_record({from_key}, {to_key})"
                )
            elif multi_ch_junction_key:
                channel["manual_map_channel_python_equiv"] = (
                    f"system_utils.map_and_record({from_key}, multi_ch_junction_key={multi_ch_junction_key})"
                )
        elif (
            require_to
            and channel.get("from_device_refdes") == to_device_refdes
            and channel.get("from_device_channel_id") == to_device_channel_id
        ):
            found_to = True
            continue  # do not add the to channel as another line in the channel map (it only exists in the from channel's row)
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
            raw_val = row.get("from_compatible_channel_type_ids", "")
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


def connector_of_channel(key):
    bom = read_bom_rows()
    refdes, channel_id = key
    device_mpn_rev = ""

    for row in bom:
        if row.get("device_ref_des") == refdes:
            device_mpn_rev = f"{row.get('MPN')}-{row.get('rev')}"
            break

    device_signals_list_path = os.path.join(
        fileio.dirpath("devices"),
        refdes,
        f"{device_mpn_rev}-signals_list.tsv",
    )
    with open(device_signals_list_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            if row.get("channel", "").strip() == channel_id.strip():
                return row.get("connector_name", "").strip()

    raise ValueError(f"Connector not found for channel {key}")


def disconnects_in_net(net):
    disconnects = []
    for connector in read_connector_list():
        if connector.get("net") == net:
            if connector.get("disconnect") == "TRUE":
                disconnects.append(connector.get("device_refdes"))
    return disconnects


def find_shortest_disconnect_chain():
    """
    For each (from_device/channel) -> (to_device/channel) in the channel map,
    find the SHORTEST series chain of disconnect devices between them and
    write it to 'disconnect_refdes_key' in the channel map TSV.
    """
    # --- Load tables ---
    with open(fileio.path("channel map"), newline="", encoding="utf-8") as f:
        channel_map = list(csv.DictReader(f, delimiter="\t"))

    with open(fileio.path("system connector list"), newline="", encoding="utf-8") as f:
        connector_list = list(csv.DictReader(f, delimiter="\t"))

    # --- Build indexes from connector_list ---
    by_device = {}  # device_refdes -> [connector,...]
    by_net = {}  # net -> [(device_refdes, connector), ...]
    net_of = {}  # (device_refdes, connector) -> net
    is_disconnect = set()  # devices flagged as disconnect

    for row in connector_list:
        dev = (row.get("device_refdes") or "").strip()
        con = (row.get("connector") or "").strip()
        net = (row.get("net") or "").strip()

        if not dev or not con:
            continue

        by_device.setdefault(dev, []).append(con)
        if net:
            by_net.setdefault(net, []).append((dev, con))
            net_of[(dev, con)] = net

        if (row.get("disconnect") or "").strip().upper() == "TRUE":
            is_disconnect.add(dev)

    # --- quick sanity checks to catch bad TSVs like the one you hit ---
    def _warn_if_suspect():
        # X5 missing?
        for ref in ["X5"]:
            if ref in is_disconnect and not any(k[0] == ref for k in net_of):
                print(
                    f"[warn] Disconnect {ref} has no connectors in system connector list."
                )

        # Example: PREAMP1 in1 & in2 should NOT be same net (unless truly shorted)
        if ("PREAMP1", "in1") in net_of and ("PREAMP1", "in2") in net_of:
            n1 = net_of[("PREAMP1", "in1")]
            n2 = net_of[("PREAMP1", "in2")]
            if n1 == n2:
                print(
                    f"[warn] PREAMP1 in1 and in2 share net '{n1}'. "
                    f"If that's not intentional, your connector list export is wrong."
                )

    _warn_if_suspect()

    # --- shortest-path search over connector nodes ---
    def _shortest_disconnect_chain(from_cn_key, to_cn_key):
        start = from_cn_key
        goal = to_cn_key

        q = deque([start])
        seen = {start}
        prev = {}

        while q:
            cur = q.popleft()
            if cur == goal:
                break

            # neighbors on the SAME NET
            net = net_of.get(cur)
            if net:
                for nxt in by_net.get(net, []):
                    if nxt not in seen:
                        seen.add(nxt)
                        prev[nxt] = cur
                        q.append(nxt)

            # neighbors on the SAME DEVICE -> ONLY if device is a disconnect
            dev, _ = cur
            if dev in is_disconnect:
                for other_con in by_device.get(dev, []):
                    nxt = (dev, other_con)
                    if nxt not in seen:
                        seen.add(nxt)
                        prev[nxt] = cur
                        q.append(nxt)

        if start != goal and goal not in prev:
            return []

        # reconstruct connector-node path
        path = [goal]
        while path[-1] != start:
            path.append(prev[path[-1]])
        path.reverse()

        # collect disconnect devices when we traverse INSIDE them
        chain = []
        for a, b in zip(path, path[1:]):
            if a[0] == b[0] and a[0] in is_disconnect:
                if not chain or chain[-1] != a[0]:
                    chain.append(a[0])
        return chain

    # --- run for each row in channel map ---
    for row in channel_map:
        from_key = (row.get("from_device_refdes"), row.get("from_device_channel_id"))
        to_key = (row.get("to_device_refdes"), row.get("to_device_channel_id"))

        # skip incomplete rows
        if not from_key[0] or not from_key[1] or not to_key[0] or not to_key[1]:
            continue

        # system_utils.connector_of_channel() lives in this module — call directly here.
        # If you're pasting this function elsewhere, replace with your import as needed.
        from_cn = (from_key[0], connector_of_channel(from_key))
        to_cn = (to_key[0], connector_of_channel(to_key))

        # optional fast path: if both ends report the same net, nothing to solve
        n_from = net_of.get(from_cn)
        n_to = net_of.get(to_cn)
        if n_from and n_to and n_from == n_to:
            # same-net: no disconnect devices required in between
            continue

        chain = _shortest_disconnect_chain(from_cn, to_cn)
        if chain:
            row["disconnect_refdes_key"] = str(chain)

    # --- write back ---
    with open(fileio.path("channel map"), "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=channel_map[0].keys(), delimiter="\t")
        writer.writeheader()
        writer.writerows(channel_map)
