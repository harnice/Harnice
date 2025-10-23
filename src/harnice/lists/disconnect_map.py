import os
import csv
from collections import deque
from harnice import fileio
from harnice.utils import system_utils

COLUMNS = [
    "A-side_device_refdes",
    "A-side_device_channel_id",
    "A-side_device_channel_type",
    "B-side_device_refdes",
    "B-side_device_channel_id",
    "B-side_device_channel_type",
    "disconnect_refdes",
    "disconnect_channel_id",
    "A-port_channel_type",
    "B-port_channel_type",
    "manual_map_channel_python_equiv",
]


def new():
    disconnect_map_rows = []

    for channel in fileio.read_tsv("channel map"):
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
                a_chan_type_id = channel.get("from_channel_type", "")
                b_refdes = channel.get("to_device_refdes", "")
                b_chan_id = channel.get("to_device_channel_id", "")
                b_chan_type_id = channel.get("to_channel_type", "")
            elif (first_port, second_port) == ("B", "A"):
                b_refdes = channel.get("from_device_refdes", "")
                b_chan_id = channel.get("from_device_channel_id", "")
                b_chan_type_id = channel.get("from_channel_type", "")
                a_refdes = channel.get("to_device_refdes", "")
                a_chan_id = channel.get("to_device_channel_id", "")
                a_chan_type_id = channel.get("to_channel_type", "")
            else:
                raise ValueError(f"Unexpected port order: {requirement}")

            disconnect_map_rows.append(
                {
                    "A-side_device_refdes": a_refdes,
                    "A-side_device_channel_id": a_chan_id,
                    "A-side_device_channel_type": a_chan_type_id,
                    "B-side_device_refdes": b_refdes,
                    "B-side_device_channel_id": b_chan_id,
                    "B-side_device_channel_type": b_chan_type_id,
                    "disconnect_refdes": refdes.strip(),
                }
            )

    for item in fileio.read_tsv("bom"):
        if item.get("disconnect"):
            disconnect_signals_list_path = os.path.join(
                fileio.dirpath("disconnects"),
                item.get("device_ref_des"),
                f"{item.get('device_ref_des')}-signals_list.tsv",
            )

            available_disconnect_channels = set()
            for signal in fileio.read_tsv(disconnect_signals_list_path):
                if signal.get("channel_id") in available_disconnect_channels:
                    continue
                available_disconnect_channels.add(signal.get("channel_id"))

                disconnect_map_rows.append(
                    {
                        "disconnect_refdes": item.get("device_ref_des"),
                        "disconnect_channel_id": signal.get("channel_id"),
                        "A-port_channel_type": signal.get("A_channel_type"),
                        "B-port_channel_type": signal.get("B_channel_type"),
                    }
                )

    with open(fileio.path("disconnect map"), "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS, delimiter="\t")
        writer.writeheader()
        writer.writerows(disconnect_map_rows)

    # initialize mapped disconnect channels set (empty TSV)
    with open(
        fileio.path("mapped disconnects set"), "w", newline="", encoding="utf-8"
    ) as f:
        pass
    with open(
        fileio.path("mapped A-side channels through disconnects set"), "w", newline="", encoding="utf-8"
    ) as f:
        pass


def assign(a_side_key, disconnect_key):
    #a_side is the (device refdes, channel_id) that is on the A-side of the disconnect
    channels = fileio.read_tsv("disconnect map")
    if channel_is_already_assigned_through_disconnect(a_side_key, disconnect_key[0]):
        raise ValueError(f"disconnect_key {disconnect_key} already assigned")

    if disconnect_is_already_assigned(disconnect_key):
        raise ValueError(f"disconnect {disconnect_key} already assigned")

    # Find the disconnect row we want to merge
    disconnect_info = None
    for row in channels:
        if (
            row.get("disconnect_refdes") == disconnect_key[0]
            and row.get("disconnect_channel_id") == disconnect_key[1]
            and row.get("A-side_device_refdes") in [None, ""]
        ):
            disconnect_info = row
            break

    updated_channels = []
    for row in channels:
        if (
            row.get("A-side_device_refdes") == a_side_key[0]
            and row.get("A-side_device_channel_id") == a_side_key[1]
            and row.get("disconnect_refdes") == disconnect_key[0]
        ):
            row["disconnect_channel_id"] = disconnect_key[1]
            row["A-port_channel_type"] = disconnect_info.get("A-port_channel_type", "")
            row["B-port_channel_type"] = disconnect_info.get("B-port_channel_type", "")
            row["manual_map_channel_python_equiv"] = (
                f"disconnect_map.assign({a_side_key}, {disconnect_key})"
            )

        elif (
            row.get("disconnect_refdes") == disconnect_key[0]
            and row.get("disconnect_channel_id") == disconnect_key[1]
            and row.get("A-side_device_refdes") in [None, ""]
        ):
            continue

        updated_channels.append(row)

    already_assigned_channels_through_disconnects_set_append(a_side_key, disconnect_key[0])
    already_assigned_disconnects_set_append(disconnect_key)

    with open(fileio.path("disconnect map"), "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS, delimiter="\t")
        writer.writeheader()
        writer.writerows(updated_channels)


def already_assigned_channels_through_disconnects_set_append(key, disconnect_refdes):
    item = f"{key}:{disconnect_refdes}"
    items = set(already_assigned_channels_through_disconnects_set())
    if item in items:
        raise ValueError(f"channel {key} through disconnect {disconnect_refdes} already assigned")
    with open(
        fileio.path("mapped A-side channels through disconnects set"), "a", newline="", encoding="utf-8"
    ) as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow([item])

def already_assigned_disconnects_set_append(key):
    items = set(already_assigned_disconnects_set())
    if str(key) in items:
        raise ValueError(f"disconnect {key} already assigned to a channel")
    items.add(str(key))
    with open(
        fileio.path("mapped disconnects set"), "w", newline="", encoding="utf-8"
    ) as f:
        writer = csv.writer(f, delimiter="\t")
        for item in sorted(items):
            writer.writerow([item])


def already_assigned_channels_through_disconnects_set():
    items = []
    with open(fileio.path("mapped A-side channels through disconnects set"), newline="", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t")
        for row in reader:
            if row and row[0].strip():  # skip blank lines
                items.append(row[0].strip())
    return items

def already_assigned_disconnects_set():
    items = []
    with open(fileio.path("mapped disconnects set"), newline="", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t")
        for row in reader:
            if row and row[0].strip():
                items.append(row[0].strip())
    return items


def add_shortest_chain_to_channel_map():
    """
    For each (from_device/channel) -> (to_device/channel) in the channel map,
    find the SHORTEST series chain of disconnect devices between them and
    write it to:
      - 'disconnect_refdes_requirement' (like "X1(A,B);X2(B,A)")
      - 'chain_of_nets' (like "WH-1;WH-2;WH-3" or a single net if no disconnects)
    """

    channel_map = fileio.read_tsv("channel map")

    by_device = {}
    by_net = {}
    net_of = {}
    is_disconnect = set()

    for row in fileio.read_tsv("system connector list"):
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

    def _shortest_disconnect_chain(from_cn_key, to_cn_key):
        start, goal = from_cn_key, to_cn_key
        q = deque([start])
        seen = {start}
        prev = {}

        while q:
            cur = q.popleft()
            if cur == goal:
                break

            net = net_of.get(cur)
            if net:
                for nxt in by_net.get(net, []):
                    if nxt not in seen:
                        seen.add(nxt)
                        prev[nxt] = cur
                        q.append(nxt)

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

        path = [goal]
        while path[-1] != start:
            path.append(prev[path[-1]])
        path.reverse()

        chain = []
        net_chain = []

        for a, b in zip(path, path[1:]):
            net_a = net_of.get(a)
            net_b = net_of.get(b)
            if net_a and net_b and net_a == net_b:
                if not net_chain or net_chain[-1] != net_a:
                    net_chain.append(net_a)

            if a[0] == b[0] and a[0] in is_disconnect:
                dev = a[0]
                port_a, port_b = a[1], b[1]

                for port in (port_a, port_b):
                    if port not in {"A", "B"}:
                        raise ValueError(
                            f"Disconnect {dev} has invalid port name '{port}'. Only 'A' and 'B' are allowed."
                        )

                if port_a == port_b:
                    raise ValueError(
                        f"Disconnect {dev} has invalid same-port traversal: {port_a}"
                    )

                chain.append(f"{dev}({port_a},{port_b})")

        return chain, net_chain

    for row in channel_map:
        from_key = (row.get("from_device_refdes"), row.get("from_device_channel_id"))
        to_key = (row.get("to_device_refdes"), row.get("to_device_channel_id"))

        if not from_key[0] or not from_key[1] or not to_key[0] or not to_key[1]:
            continue

        from_cn = (from_key[0], system_utils.connector_of_channel(from_key))
        to_cn = (to_key[0], system_utils.connector_of_channel(to_key))

        n_from = net_of.get(from_cn)
        n_to = net_of.get(to_cn)

        if n_from and n_to and n_from == n_to:
            row["disconnect_refdes_requirement"] = ""
            row["chain_of_nets"] = n_from
            continue

        chain, net_chain = _shortest_disconnect_chain(from_cn, to_cn)
        if chain or net_chain:
            row["disconnect_refdes_requirement"] = ";".join(chain)
            row["chain_of_nets"] = ";".join(net_chain)

    with open(fileio.path("channel map"), "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=channel_map[0].keys(), delimiter="\t")
        writer.writeheader()
        writer.writerows(channel_map)

def channel_is_already_assigned_through_disconnect(key, disconnect_refdes):
    if f"{str(key)}:{disconnect_refdes}" in already_assigned_channels_through_disconnects_set():
        return True
    else:
        return False

def disconnect_is_already_assigned(key):
    if str(key) in already_assigned_disconnects_set():
        return True
    else:
        return False