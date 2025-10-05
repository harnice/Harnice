from harnice import (
    fileio,
    component_library,
    mapped_channels,
    mapped_disconnect_channels,
    icd,
)
import os
import csv
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
    "disconnect_refdes_requirement",
    "chain_of_nets",
    "manual_map_channel_python_equiv",
]

DISCONNECT_CHANNEL_MAP_COLUMNS = [
    "A-side_device_refdes",
    "A-side_device_channel_id",
    "A-side_device_channel_type_id",
    "A-side_device_compatible_channel_type_ids",
    "B-side_device_refdes",
    "B-side_device_channel_id",
    "B-side_device_channel_type_id",
    "B-side_device_compatible_channel_type_ids",
    "disconnect_refdes",
    "disconnect_channel_id",
    "A-port_channel_type",
    "A-port_compatible_channel_type_ids",
    "B-port_channel_type",
    "B-port_compatible_channel_type_ids",
    "manual_map_channel_python_equiv",
]

CIRCUITS_LIST_COLUMNS = [
    "net",
    "circuit_id",
    "signal",
    "net_from_refdes",
    "net_from_channel_id",
    "net_from_connector_name",
    "net_from_contact",
    "net_to_refdes",
    "net_to_channel_id",
    "net_to_connector_name",
    "net_to_contact",
    "from_side_device_refdes",
    "from_side_device_chname",
    "to_side_device_refdes",
    "to_side_device_chname",
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


def map_and_record_disconnect(a_side_key, disconnect_key):
    map_channel_to_disconnect_channel(a_side_key, disconnect_key)
    mapped_disconnect_channels.append(disconnect_key)


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

    # load connector list
    with open(fileio.path("system connector list"), newline="", encoding="utf-8") as f:
        connector_list = list(csv.DictReader(f, delimiter="\t"))

    for connector in connector_list:
        device_refdes = connector.get("device_refdes")

        # signals list path
        if connector.get("disconnect") == "TRUE":
            # don't want disconnects to show up in channel map
            continue
        else:
            device_signals_list_path = os.path.join(
                fileio.dirpath("devices"),
                device_refdes,
                f"{device_refdes}-signals_list.tsv",
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
        raw = (channel.get("disconnect_refdes_requirement") or "").strip()
        if not raw:
            continue

        # split on semicolon -> one row per disconnect_refdes requirement
        disconnects = [item.strip() for item in raw.split(";") if item.strip()]

        for requirement in disconnects:
            # requirement looks like "X1(A,B)" or "X2(B,A)"
            refdes, ports = requirement.split("(")
            ports = ports.rstrip(")")
            first_port, second_port = [p.strip() for p in ports.split(",")]

            # orientation: (A,B) means from_device is A-side, (B,A) means from_device is B-side
            if (first_port, second_port) == ("A", "B"):
                a_refdes = channel.get("from_device_refdes", "")
                a_chan_id = channel.get("from_device_channel_id", "")
                a_chan_type_id = channel.get("from_channel_type_id", "")
                a_chan_compatible_channel_type_ids = channel.get(
                    "from_compatible_channel_type_ids", ""
                )
                b_refdes = channel.get("to_device_refdes", "")
                b_chan_id = channel.get("to_device_channel_id", "")
                b_chan_type_id = channel.get("to_channel_type_id", "")
                b_chan_compatible_channel_type_ids = channel.get(
                    "to_compatible_channel_type_ids", ""
                )
            elif (first_port, second_port) == ("B", "A"):
                b_refdes = channel.get("from_device_refdes", "")
                b_chan_id = channel.get("from_device_channel_id", "")
                b_chan_type_id = channel.get("from_channel_type_id", "")
                b_chan_compatible_channel_type_ids = channel.get(
                    "from_compatible_channel_type_ids", ""
                )
                a_refdes = channel.get("to_device_refdes", "")
                a_chan_id = channel.get("to_device_channel_id", "")
                a_chan_type_id = channel.get("to_channel_type_id", "")
                a_chan_compatible_channel_type_ids = channel.get(
                    "to_compatible_channel_type_ids", ""
                )
            else:
                raise ValueError(f"Unexpected port order: {requirement}")

            disconnect_channel_map.append(
                {
                    "A-side_device_refdes": a_refdes,
                    "A-side_device_channel_id": a_chan_id,
                    "A-side_device_channel_type_id": a_chan_type_id,
                    "A-side_device_compatible_channel_type_ids": a_chan_compatible_channel_type_ids,
                    "B-side_device_refdes": b_refdes,
                    "B-side_device_channel_id": b_chan_id,
                    "B-side_device_channel_type_id": b_chan_type_id,
                    "B-side_device_compatible_channel_type_ids": b_chan_compatible_channel_type_ids,
                    "disconnect_refdes": refdes.strip(),
                }
            )

    # load BOM
    with open(fileio.path("bom"), newline="", encoding="utf-8") as f:
        bom = list(csv.DictReader(f, delimiter="\t"))

    for item in bom:
        if item.get("disconnect"):
            disconnect_signals_list_path = os.path.join(
                fileio.dirpath("disconnects"),
                item.get("device_ref_des"),
                f"{item.get("device_ref_des")}-signals_list.tsv",
            )
            with open(disconnect_signals_list_path, newline="", encoding="utf-8") as f:
                disconnect_signals = list(csv.DictReader(f, delimiter="\t"))

            available_disconnect_channels = set()
            for signal in disconnect_signals:
                if signal.get("channel") in available_disconnect_channels:
                    continue
                available_disconnect_channels.add(signal.get("channel"))

                disconnect_channel_map.append(
                    {
                        "disconnect_refdes": item.get("device_ref_des"),
                        "disconnect_channel_id": signal.get("channel"),
                        "A-port_channel_type": signal.get("A_channel_type_id"),
                        "A-port_compatible_channel_type_ids": signal.get(
                            "A_compatible_channel_type_ids"
                        ),
                        "B-port_channel_type": signal.get("B_channel_type_id"),
                        "B-port_compatible_channel_type_ids": signal.get(
                            "B_compatible_channel_type_ids"
                        ),
                    }
                )

    with open(
        fileio.path("disconnect channel map"), "w", newline="", encoding="utf-8"
    ) as f:
        writer = csv.DictWriter(
            f, fieldnames=DISCONNECT_CHANNEL_MAP_COLUMNS, delimiter="\t"
        )
        writer.writeheader()
        writer.writerows(disconnect_channel_map)


def read_channel_map():
    with open(fileio.path("channel map"), "r", encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def map_channel(from_key, to_key=None, multi_ch_junction_key=""):
    channels = read_channel_map()

    to_channel = None
    for channel in channels:
        if (
            channel.get("from_device_refdes") == to_key[0]
            and channel.get("from_device_channel_id") == to_key[1]
        ):
            to_channel = channel
            break

    from_channel = None
    for channel in channels:
        if (
            channel.get("from_device_refdes") == from_key[0]
            and channel.get("from_device_channel_id") == from_key[1]
        ):
            from_channel = channel
            break

    # you have to have at least a to channel or a multi_ch_junction_key, can't map from to nothing
    if not to_channel and multi_ch_junction_key == (""):
        raise ValueError(f"to_key {to_key} not found in channel map")
    else:
        require_to = bool(to_key[0] or to_key[1])
    # find the a compatible channel and write it to the from channel
    updated_channels, found_from, found_to = [], False, False

    for from_channel in channels:
        if (
            from_channel.get("from_device_refdes") == from_key[0]
            and from_channel.get("from_device_channel_id") == from_key[1]
        ):
            from_channel["to_device_refdes"] = to_key[0]
            from_channel["to_device_channel_id"] = to_key[1]
            from_channel["to_channel_type_id"] = to_channel.get("from_channel_type_id")
            from_channel["to_compatible_channel_type_ids"] = to_channel.get(
                "from_compatible_channel_type_ids"
            )
            if multi_ch_junction_key:
                from_channel["multi_ch_junction_id"] = multi_ch_junction_key
            found_from = True
            # add python equivalent to channel map to help user grab this map and force its use here or elsewhere
            if require_to:
                from_channel["manual_map_channel_python_equiv"] = (
                    f"system_utils.map_and_record({from_key}, {to_key})"
                )
            elif multi_ch_junction_key:
                from_channel["manual_map_channel_python_equiv"] = (
                    f"system_utils.map_and_record({from_key}, multi_ch_junction_key={multi_ch_junction_key})"
                )
        elif (
            require_to
            and from_channel.get("from_device_refdes") == to_key[0]
            and from_channel.get("from_device_channel_id") == to_key[1]
        ):
            found_to = True
            continue  # do not add the to channel as another line in the channel map (it only exists in the from channel's row)
        updated_channels.append(from_channel)

    if not found_from:
        raise ValueError(f"from_key {from_key} not found in channel map")
    if require_to and not found_to:
        raise ValueError(f"to_key {to_key} not found in channel map")

    with open(fileio.path("channel map"), "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CHANNEL_MAP_COLUMNS, delimiter="\t")
        writer.writeheader()
        writer.writerows(updated_channels)


def map_channel_to_disconnect_channel(a_side_key, disconnect_key):
    # Load all rows
    with open(fileio.path("disconnect channel map"), "r", encoding="utf-8") as f:
        channels = list(csv.DictReader(f, delimiter="\t"))

    # Find the disconnect row we want to merge
    disconnect_info = None
    for row in channels:
        if (
            row.get("disconnect_refdes") == disconnect_key[0]
            and row.get("disconnect_channel_id") == disconnect_key[1]
            and row.get("A-side_device_refdes")
            in [None, ""]  # otherwise it might find an already mapped channel
        ):
            disconnect_info = row
            break

    updated_channels = []
    for row in channels:
        # Case 1: row matches the A-side device/channel -> update it with disconnect info
        if (
            row.get("A-side_device_refdes") == a_side_key[0]
            and row.get("A-side_device_channel_id") == a_side_key[1]
            and row.get("disconnect_refdes") == disconnect_key[0]
        ):
            row["disconnect_channel_id"] = disconnect_key[1]
            row["A-port_channel_type"] = disconnect_info.get("A-port_channel_type", "")
            row["A-port_compatible_channel_type_ids"] = disconnect_info.get(
                "A-port_compatible_channel_type_ids", ""
            )
            row["B-port_channel_type"] = disconnect_info.get("B-port_channel_type", "")
            row["B-port_compatible_channel_type_ids"] = disconnect_info.get(
                "B-port_compatible_channel_type_ids", ""
            )

            row["manual_map_channel_python_equiv"] = (
                f"system_utils.map_and_record_disconnect({a_side_key}, {disconnect_key})"
            )

        elif (
            row.get("disconnect_refdes") == disconnect_key[0]
            and row.get("disconnect_channel_id") == disconnect_key[1]
            and row.get("A-side_device_refdes") in [None, ""]
        ):
            continue

        updated_channels.append(row)

    # Write the updated table back
    with open(
        fileio.path("disconnect channel map"), "w", newline="", encoding="utf-8"
    ) as f:
        writer = csv.DictWriter(
            f, fieldnames=DISCONNECT_CHANNEL_MAP_COLUMNS, delimiter="\t"
        )
        writer.writeheader()
        writer.writerows(updated_channels)


def mpn_of_device_refdes(refdes):
    for row in read_bom_rows():
        if row.get("device_ref_des") == refdes:
            return row.get("MFG"), row.get("MPN"), row.get("rev")
    return None, None, None


def connector_of_channel(key):
    refdes, channel_id = key

    device_signals_list_path = os.path.join(
        fileio.dirpath("devices"),
        refdes,
        f"{refdes}-signals_list.tsv",
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
    write it to:
      - 'disconnect_refdes_requirement' (like "X1(A,B);X2(B,A)")
      - 'chain_of_nets' (like "WH-1;WH-2;WH-3" or a single net if no disconnects)
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

    # --- sanity checks ---
    def _warn_if_suspect():
        for ref in ["X5"]:
            if ref in is_disconnect and not any(k[0] == ref for k in net_of):
                print(
                    f"[warn] Disconnect {ref} has no connectors in system connector list."
                )

        if ("PREAMP1", "in1") in net_of and ("PREAMP1", "in2") in net_of:
            n1 = net_of[("PREAMP1", "in1")]
            n2 = net_of[("PREAMP1", "in2")]
            if n1 == n2:
                print(
                    f"[warn] PREAMP1 in1 and in2 share net '{n1}'. "
                    f"If that's not intentional, your connector list export is wrong."
                )

    _warn_if_suspect()

    # --- shortest-path search ---
    def _shortest_disconnect_chain(from_cn_key, to_cn_key):
        start, goal = from_cn_key, to_cn_key

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

            # neighbors on the SAME DEVICE (only for disconnects)
            dev, _ = cur
            if dev in is_disconnect:
                for other_con in by_device.get(dev, []):
                    nxt = (dev, other_con)
                    if nxt not in seen:
                        seen.add(nxt)
                        prev[nxt] = cur
                        q.append(nxt)

        if start != goal and goal not in prev:
            return [], []

        # reconstruct connector-node path
        path = [goal]
        while path[-1] != start:
            path.append(prev[path[-1]])
        path.reverse()

        # collect disconnect devices and nets
        chain = []
        net_chain = []

        for a, b in zip(path, path[1:]):
            # record nets between steps
            net_a = net_of.get(a)
            net_b = net_of.get(b)
            if net_a and net_b and net_a == net_b:
                if not net_chain or net_chain[-1] != net_a:
                    net_chain.append(net_a)

            # record disconnect traversals
            if a[0] == b[0] and a[0] in is_disconnect:
                dev = a[0]
                port_a, port_b = a[1], b[1]

                # enforce A/B only
                for port in (port_a, port_b):
                    if port not in {"A", "B"}:
                        raise ValueError(
                            f"Disconnect {dev} has invalid port name '{port}'. "
                            "Only 'A' and 'B' are allowed."
                        )

                if port_a == port_b:
                    raise ValueError(
                        f"Disconnect {dev} has invalid same-port traversal: {port_a}"
                    )

                chain.append(f"{dev}({port_a},{port_b})")

        return chain, net_chain

    # --- run for each row in channel map ---
    for row in channel_map:
        from_key = (row.get("from_device_refdes"), row.get("from_device_channel_id"))
        to_key = (row.get("to_device_refdes"), row.get("to_device_channel_id"))

        # skip incomplete rows
        if not from_key[0] or not from_key[1] or not to_key[0] or not to_key[1]:
            continue

        from_cn = (from_key[0], connector_of_channel(from_key))
        to_cn = (to_key[0], connector_of_channel(to_key))

        n_from = net_of.get(from_cn)
        n_to = net_of.get(to_cn)

        if n_from and n_to and n_from == n_to:
            # same-net: no disconnect devices required in between
            row["disconnect_refdes_requirement"] = ""
            row["chain_of_nets"] = n_from  # singular net
            continue

        chain, net_chain = _shortest_disconnect_chain(from_cn, to_cn)
        if chain or net_chain:
            row["disconnect_refdes_requirement"] = ";".join(chain)
            row["chain_of_nets"] = ";".join(net_chain)

    # --- write back ---
    with open(fileio.path("channel map"), "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=channel_map[0].keys(), delimiter="\t")
        writer.writeheader()
        writer.writerows(channel_map)


def make_circuits_list():
    # --- load channel map ---
    with open(fileio.path("channel map"), newline="", encoding="utf-8") as f:
        channel_map = list(csv.DictReader(f, delimiter="\t"))

    circuits_list = []
    circuit_id = 0

    # resolvers
    def resolve_device_endpoint(refdes, channel_id, signal):
        slp = os.path.join(fileio.dirpath("devices"), refdes, f"{refdes}-signals_list.tsv")
        connector = icd.connector_name_of_channel(channel_id, slp) if channel_id else ""
        contact   = icd.pin_of_signal(signal, slp) if channel_id else ""
        return {"refdes": refdes, "channel_id": channel_id, "connector_name": connector, "contact": contact}

    def resolve_disconnect_endpoint(refdes, side, signal):
        """side must be 'A' or 'B'."""
        slp = os.path.join(fileio.dirpath("disconnects"), refdes, f"{refdes}-signals_list.tsv")
        with open(slp, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f, delimiter="\t"))
        row = next((r for r in rows if (r.get("signal") or "").strip() == signal), None)
        if row is None:
            raise ValueError(f"{refdes}-signals_list.tsv has no row for signal='{signal}'")
        ch_id = (row.get("channel") or "").strip()
        if side == "A":
            contact = (row.get("A_contact") or "").strip()
        elif side == "B":
            contact = (row.get("B_contact") or "").strip()
        else:
            raise ValueError(f"Invalid side '{side}' for disconnect {refdes}")
        return {"refdes": refdes, "channel_id": ch_id, "connector_name": side, "contact": contact}

    # --- iterate channel rows ---
    for m in channel_map:
        if not m.get("from_device_channel_id"):
            continue
        if not m.get("to_device_refdes") and not m.get("multi_ch_junction_id"):
            continue

        from_dev = m["from_device_refdes"]
        from_ch  = m["from_device_channel_id"]
        to_dev   = m["to_device_refdes"]
        to_ch    = m["to_device_channel_id"]

        # signals of the channel (fan out)
        signals = icd.signals_of_channel(from_ch, from_dev)

        # parse disconnect requirement: X1(A,B);X5(A,B) ...
        dis_chain = []
        if m.get("disconnect_refdes_requirement"):
            for tok in m["disconnect_refdes_requirement"].split(";"):
                tok = tok.strip()
                if not tok:
                    continue
                refdes, sides = tok.split("(", 1)
                refdes = refdes.strip()
                sides  = sides.rstrip(")")
                side_from, side_to = [s.strip() for s in sides.split(",")]
                dis_chain.append((refdes, side_from, side_to))
        dis_set = {d[0] for d in dis_chain}

        # nets chain (one per *net segment*)
        nets_chain = []
        if m.get("chain_of_nets"):
            nets_chain = [n.strip() for n in m["chain_of_nets"].split(";") if n.strip()]

        # path encoded as disconnect hops then final device
        hops = dis_chain + [(to_dev, None, None)]

        for sig in signals:
            net_i = 0
            # current node before first segment is the from device
            cur_refdes = from_dev
            cur_side   = None     # only meaningful when current node is a disconnect
            cur_chid   = from_ch  # channel id when at a device

            for hop in hops:
                net = nets_chain[net_i] if net_i < len(nets_chain) else ""

                if hop[1] is not None:
                    # --- this segment leads INTO the disconnect on side_from ---
                    refdes, side_from, side_to = hop

                    # left endpoint (current node)
                    if cur_refdes in dis_set:
                        left = resolve_disconnect_endpoint(cur_refdes, cur_side, sig)
                    else:
                        left = resolve_device_endpoint(cur_refdes, cur_chid, sig)

                    # right endpoint is the disconnect's *entering* side
                    right = resolve_disconnect_endpoint(refdes, side_from, sig)

                    # record circuit row for this net segment
                    circuits_list.append({
                        "net": net,
                        "circuit_id": circuit_id,
                        "signal": sig,
                        "net_from_refdes": left["refdes"],
                        "net_from_channel_id": left["channel_id"],
                        "net_from_connector_name": left["connector_name"],
                        "net_from_contact": left["contact"],
                        "net_to_refdes": right["refdes"],
                        "net_to_channel_id": right["channel_id"],
                        "net_to_connector_name": right["connector_name"],  # A (entering side)
                        "net_to_contact": right["contact"],
                        "from_side_device_refdes": m["from_device_refdes"],
                        "from_side_device_chname": m["from_device_channel_id"],
                        "to_side_device_refdes": m["to_device_refdes"],
                        "to_side_device_chname": m["to_device_channel_id"],
                    })
                    circuit_id += 1
                    net_i += 1

                    # after crossing the disconnect internally, the *current node*
                    # becomes the disconnect's EXIT side (side_to). the channel id
                    # is the same "channel" value from its signals list.
                    cur_refdes = refdes
                    cur_side   = side_to
                    cur_chid   = right["channel_id"]

                else:
                    # --- final segment goes from current node to the final device ---
                    to_refdes, _, _ = hop

                    if cur_refdes in dis_set:
                        left = resolve_disconnect_endpoint(cur_refdes, cur_side, sig)
                    else:
                        left = resolve_device_endpoint(cur_refdes, cur_chid, sig)

                    right = resolve_device_endpoint(to_refdes, to_ch, sig)

                    circuits_list.append({
                        "net": net,
                        "circuit_id": circuit_id,
                        "signal": sig,
                        "net_from_refdes": left["refdes"],
                        "net_from_channel_id": left["channel_id"],
                        "net_from_connector_name": left["connector_name"],
                        "net_from_contact": left["contact"],
                        "net_to_refdes": right["refdes"],
                        "net_to_channel_id": right["channel_id"],
                        "net_to_connector_name": right["connector_name"],
                        "net_to_contact": right["contact"],
                        "from_side_device_refdes": m["from_device_refdes"],
                        "from_side_device_chname": m["from_device_channel_id"],
                        "to_side_device_refdes": m["to_device_refdes"],
                        "to_side_device_chname": m["to_device_channel_id"],
                    })
                    circuit_id += 1
                    net_i += 1

                    # done with this channel row

    # --- write file ---
    with open(fileio.path("circuits list"), "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CIRCUITS_LIST_COLUMNS, delimiter="\t")
        writer.writeheader()
        writer.writerows(circuits_list)
