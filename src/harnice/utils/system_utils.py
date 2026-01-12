import os
import csv
from collections import deque
from harnice import fileio
from harnice.lists import instances_list
from harnice.utils import library_utils


def mpn_of_device_refdes(refdes):
    """
    Looks up manufacturer part number information for a device reference designator.

    Searches the BOM (Bill of Materials) for a device with the given reference designator
    and returns its manufacturer, part number, and revision.

    **Args:**
    - `refdes` (str): Device reference designator to look up (e.g., `"J1"`, `"X1"`).

    **Returns:**
    - `tuple`: A tuple of `(MFG, MPN, rev)` if found, or `(None, None, None)` if not found.
    """
    for row in fileio.read_tsv("bom"):
        if row.get("device_refdes") == refdes:
            return row.get("MFG"), row.get("MPN"), row.get("rev")
    return None, None, None


def connector_of_channel(key):
    """
    Finds the connector name associated with a device channel.

    Given a device reference designator and channel ID tuple, looks up the corresponding
    connector name from the device's signals list.

    **Args:**
    - `key` (tuple): A tuple of `(device_refdes, channel_id)` identifying the channel.

    **Returns:**
    - `str`: The connector name associated with the channel.

    **Raises:**
    - `ValueError`: If the connector is not found for the given channel.
    """
    refdes, channel_id = key

    device_signals_list_path = os.path.join(
        fileio.dirpath("instance_data"),
        "device",
        refdes,
        f"{refdes}-signals_list.tsv",
    )
    for row in fileio.read_tsv(device_signals_list_path):
        if row.get("channel_id", "").strip() == channel_id.strip():
            return row.get("connector_name", "").strip()

    raise ValueError(f"Connector not found for channel {key}")


def find_connector_with_no_circuit(connector_list, circuits_list):
    """
    Validates that all connectors have associated circuits.

    Checks each connector in the connector list to ensure it has at least one
    corresponding circuit in the circuits list. Skips connectors with `"unconnected"`
    in their net name. Raises an error if any connector lacks a circuit.

    **Args:**
    - `connector_list` (list): List of connector dictionaries from the system connector list.
    - `circuits_list` (list): List of circuit dictionaries from the circuits list.

    **Raises:**
    - `ValueError`: If a connector is found that has no associated circuits. The error
        message suggests checking the channel map and channel compatibility.
    """
    for connector in connector_list:
        device_refdes = connector.get("device_refdes", "").strip()
        connector_name = connector.get("connector", "").strip()

        # skip if either key is missing
        if not device_refdes or not connector_name:
            continue

        # skip device if net name contains "unconnected"
        if "unconnected" in connector.get("net", "").strip():
            continue

        found_match = False
        for circuit in circuits_list:
            from_device_refdes = circuit.get("net_from_refdes", "").strip()
            from_connector_name = circuit.get("net_from_connector_name", "").strip()
            to_device_refdes = circuit.get("net_to_refdes", "").strip()
            to_connector_name = circuit.get("net_to_connector_name", "").strip()

            if (
                from_device_refdes == device_refdes
                and from_connector_name == connector_name
            ) or (
                to_device_refdes == device_refdes
                and to_connector_name == connector_name
            ):
                found_match = True
                break

        if not found_match:
            raise ValueError(
                f"Connector '{connector_name}' of device '{device_refdes}' does not contain any circuits. Check if it was mapped in the channel map. If n, check channel compatibility."
            )


def make_instances_for_connectors_cavities_nodes_channels_circuits():
    """
    Creates instances for all system components based on circuits.

    This function processes the circuits list and creates instances in the instances list
    for all connectors, connector cavities, nodes, channels, and circuits in the system.
    For each circuit, it creates:

    - Connector nodes (at both ends)
    - Connector instances (at both ends)
    - Connector cavity instances (at both ends)
    - Circuit instance
    - Channel instance
    - Net-channel instances for each net in the channel chain

    The function reads from the circuits list, system connector list, and channel map
    to build the complete instance hierarchy.
    """
    connectors_list = fileio.read_tsv("system connector list")
    channel_map = fileio.read_tsv("channel map")

    for circuit in fileio.read_tsv("circuits list"):
        from_connector_key = (
            f"{circuit.get('net_from_refdes')}.{circuit.get('net_from_connector_name')}"
        )
        from_cavity = f"{circuit.get('net_from_refdes')}.{circuit.get('net_from_connector_name')}.{circuit.get('net_from_cavity')}"

        from_connector_mpn = ""
        for connector in connectors_list:
            if connector.get("device_refdes") == circuit.get(
                "net_from_refdes"
            ) and connector.get("connector") == circuit.get("net_from_connector_name"):
                from_connector_mpn = connector.get("connector_mpn")
                break

        # from connector node
        instances_list.new_instance(
            f"{from_connector_key}.node",
            {
                "net": circuit.get("net"),
                "item_type": "node",
                "location_type": "node",
                "connector_group": from_connector_key,
            },
            ignore_duplicates=True,
        )

        # from connector
        instances_list.new_instance(
            f"{from_connector_key}.conn",
            {
                "net": circuit.get("net"),
                "item_type": "connector",
                "location_type": "node",
                "connector_group": from_connector_key,
                "parent_csys_instance_name": f"{from_connector_key}.node",
                "parent_csys_outputcsys_name": "origin",
                "this_instance_mating_device_refdes": circuit.get("net_from_refdes"),
                "this_instance_mating_device_connector": circuit.get(
                    "net_from_connector_name"
                ),
                "this_instance_mating_device_connector_mpn": from_connector_mpn,
            },
            ignore_duplicates=True,
        )

        # from connector cavity
        instances_list.new_instance(
            from_cavity,
            {
                "net": circuit.get("net"),
                "item_type": "connector_cavity",
                "parent_instance": f"{from_connector_key}.conn",  # from connector instance
                "location_type": "node",
                "connector_group": from_connector_key,
                "circuit_id": circuit.get("circuit_id"),
                "circuit_port_number": 0,
            },
            ignore_duplicates=True,
        )

        to_connector_key = (
            f"{circuit.get('net_to_refdes')}.{circuit.get('net_to_connector_name')}"
        )
        to_cavity = f"{circuit.get('net_to_refdes')}.{circuit.get('net_to_connector_name')}.{circuit.get('net_to_cavity')}"

        to_connector_mpn = ""
        for connector in connectors_list:
            if connector.get("device_refdes") == circuit.get(
                "net_to_refdes"
            ) and connector.get("connector") == circuit.get("net_to_connector_name"):
                to_connector_mpn = connector.get("connector_mpn")
                break

        # to connector node
        instances_list.new_instance(
            f"{to_connector_key}.node",
            {
                "net": circuit.get("net"),
                "item_type": "node",
                "location_type": "node",
                "connector_group": to_connector_key,
            },
            ignore_duplicates=True,
        )

        # to connector
        instances_list.new_instance(
            f"{to_connector_key}.conn",
            {
                "net": circuit.get("net"),
                "item_type": "connector",
                "location_type": "node",
                "connector_group": to_connector_key,
                "parent_csys_instance_name": f"{to_connector_key}.node",
                "parent_csys_outputcsys_name": "origin",
                "this_instance_mating_device_refdes": circuit.get("net_to_refdes"),
                "this_instance_mating_device_connector": circuit.get(
                    "net_to_connector_name"
                ),
                "this_instance_mating_device_connector_mpn": to_connector_mpn,
            },
            ignore_duplicates=True,
        )

        # to connector cavity
        instances_list.new_instance(
            to_cavity,
            {
                "net": circuit.get("net"),
                "item_type": "connector_cavity",
                "parent_instance": f"{to_connector_key}.conn",  # to connector instance
                "location_type": "node",
                "connector_group": to_connector_key,
                "circuit_id": circuit.get("circuit_id"),
                "circuit_port_number": 1,
            },
            ignore_duplicates=True,
        )

        # add circuit
        instances_list.new_instance(
            f"circuit-{circuit.get('circuit_id')}",
            {
                "net": circuit.get("net"),
                "item_type": "circuit",
                "channel_group": f"channel-{circuit.get('from_side_device_refdes')}.{circuit.get('from_side_device_chname')}-{circuit.get('to_side_device_refdes')}.{circuit.get('to_side_device_chname')}",
                "circuit_id": circuit.get("circuit_id"),
                "node_at_end_a": from_cavity,
                "node_at_end_b": to_cavity,
                "this_net_from_device_refdes": circuit.get("net_from_refdes"),
                "this_net_from_device_channel_id": circuit.get("net_from_channel_id"),
                "this_net_from_device_connector_name": circuit.get(
                    "net_from_connector_name"
                ),
                "this_net_to_device_refdes": circuit.get("net_to_refdes"),
                "this_net_to_device_channel_id": circuit.get("net_to_channel_id"),
                "this_net_to_device_connector_name": circuit.get(
                    "net_to_connector_name"
                ),
                "this_channel_from_device_refdes": circuit.get(
                    "from_side_device_refdes"
                ),
                "this_channel_from_device_channel_id": circuit.get(
                    "from_side_device_chname"
                ),
                "this_channel_to_device_refdes": circuit.get("to_side_device_refdes"),
                "this_channel_to_device_channel_id": circuit.get(
                    "to_side_device_chname"
                ),
                "this_channel_from_channel_type": circuit.get("from_channel_type"),
                "this_channel_to_channel_type": circuit.get("to_channel_type"),
                "signal_of_channel_type": circuit.get("signal"),
            },
            ignore_duplicates=True,
        )

        # --- add channel
        instances_list.new_instance(
            f"channel-{circuit.get('from_side_device_refdes')}.{circuit.get('from_side_device_chname')}-"
            f"{circuit.get('to_side_device_refdes')}.{circuit.get('to_side_device_chname')}",
            {
                "item_type": "channel",
                "channel_group": (
                    f"channel-{circuit.get('from_side_device_refdes')}.{circuit.get('from_side_device_chname')}-"
                    f"{circuit.get('to_side_device_refdes')}.{circuit.get('to_side_device_chname')}"
                ),
                "location_type": "segment",
                "this_net_from_device_refdes": circuit.get("net_from_refdes"),
                "this_net_from_device_channel_id": circuit.get("net_from_channel_id"),
                "this_net_from_device_connector_name": circuit.get(
                    "net_from_connector_name"
                ),
                "this_net_to_device_refdes": circuit.get("net_to_refdes"),
                "this_net_to_device_channel_id": circuit.get("net_to_channel_id"),
                "this_net_to_device_connector_name": circuit.get(
                    "net_to_connector_name"
                ),
                "this_channel_from_device_refdes": circuit.get(
                    "from_side_device_refdes"
                ),
                "this_channel_from_device_channel_id": circuit.get(
                    "from_side_device_chname"
                ),
                "this_channel_to_device_refdes": circuit.get("to_side_device_refdes"),
                "this_channel_to_device_channel_id": circuit.get(
                    "to_side_device_chname"
                ),
                "this_channel_from_channel_type": circuit.get("from_channel_type"),
                "this_channel_to_channel_type": circuit.get("to_channel_type"),
            },
            ignore_duplicates=True,
        )
        for channel in channel_map:
            if (
                channel.get("from_device_refdes")
                == circuit.get("from_side_device_refdes")
                and channel.get("from_device_channel_id")
                == circuit.get("from_side_device_chname")
                and channel.get("to_device_refdes")
                == circuit.get("to_side_device_refdes")
                and channel.get("to_device_channel_id")
                == circuit.get("to_side_device_chname")
            ):
                chain_of_nets = (channel.get("chain_of_nets") or "").split(";")
                chain_of_connectors = (channel.get("chain_of_connectors") or "").split(
                    ";"
                )
                break

        # --- process each net in the channel chain
        for net in chain_of_nets:
            # Find all connectors associated with this net
            connectors_for_net = [
                item.split(".", 1)[1]
                for item in chain_of_connectors
                if item.startswith(f"{net}.")
            ]

            node_a = node_b = ""
            if connectors_for_net:
                first = connectors_for_net[0]
                last = connectors_for_net[-1]

                # Each connector looks like "J1A" or "X1B"
                # Split into refdes + connector suffix if possible
                def split_connector(fullname):
                    # Find where letters end / digits start
                    for i, ch in enumerate(fullname):
                        if ch.isalpha() and i > 0 and fullname[i - 1].isdigit():
                            return fullname[:i], fullname[i:]
                    return fullname, ""

                dev_a, port_a = split_connector(first)
                dev_b, port_b = split_connector(last)

                node_a = f"{dev_a}.{port_a}.conn" if port_a else f"{dev_a}.conn"
                node_b = f"{dev_b}.{port_b}.conn" if port_b else f"{dev_b}.conn"

            # --- create instance for this net
            instances_list.new_instance(
                f"net{net}:channel-{circuit.get('from_side_device_refdes')}.{circuit.get('from_side_device_chname')}-"
                f"{circuit.get('to_side_device_refdes')}.{circuit.get('to_side_device_chname')}",
                {
                    "net": net,
                    "item_type": "net-channel",
                    "channel_group": (
                        f"channel-{circuit.get('from_side_device_refdes')}.{circuit.get('from_side_device_chname')}-"
                        f"{circuit.get('to_side_device_refdes')}.{circuit.get('to_side_device_chname')}"
                    ),
                    "location_type": "segment",
                    "parent_instance": f"channel-{circuit.get('from_side_device_refdes')}.{circuit.get('from_side_device_chname')}-{circuit.get('to_side_device_refdes')}.{circuit.get('to_side_device_chname')}",
                    "node_at_end_a": node_a,
                    "node_at_end_b": node_b,
                    "this_net_from_device_refdes": circuit.get("net_from_refdes"),
                    "this_net_from_device_channel_id": circuit.get(
                        "net_from_channel_id"
                    ),
                    "this_net_from_device_connector_name": circuit.get(
                        "net_from_connector_name"
                    ),
                    "this_net_to_device_refdes": circuit.get("net_to_refdes"),
                    "this_net_to_device_channel_id": circuit.get("net_to_channel_id"),
                    "this_net_to_device_connector_name": circuit.get(
                        "net_to_connector_name"
                    ),
                    "this_channel_from_device_refdes": circuit.get(
                        "from_side_device_refdes"
                    ),
                    "this_channel_from_device_channel_id": circuit.get(
                        "from_side_device_chname"
                    ),
                    "this_channel_to_device_refdes": circuit.get(
                        "to_side_device_refdes"
                    ),
                    "this_channel_to_device_channel_id": circuit.get(
                        "to_side_device_chname"
                    ),
                    "this_channel_from_channel_type": circuit.get("from_channel_type"),
                    "this_channel_to_channel_type": circuit.get("to_channel_type"),
                },
                ignore_duplicates=True,
            )

    for connector in fileio.read_tsv("system connector list"):
        try:
            instances_list.modify(
                f"{connector.get('device_refdes')}.{connector.get('connector')}.conn",
                {
                    "this_instance_mating_device_refdes": connector.get(
                        "device_refdes"
                    ),
                    "this_instance_mating_device_connector": connector.get("connector"),
                    "this_instance_mating_device_connector_mpn": connector.get(
                        "connector_mpn"
                    ),
                },
            )
        except ValueError:
            pass


def add_chains_to_channel_map():
    """
    For each (from_device/channel) -> (to_device/channel) in the channel map,
    find:
      - 'disconnect_refdes_requirement' (like "X1(A,B);X2(B,A)")
      - 'chain_of_nets' (like "WH-1;WH-2;WH-3" or a single net if no disconnects)
      - 'chain_of_connectors' (like "WH-1.J1A;WH-2.X1A;WH-2.X1B;WH-3.J2A")
    """

    channel_map = fileio.read_tsv("channel map")
    by_device, by_net, net_of, is_disconnect = {}, {}, {}, set()

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
        q, seen, prev = deque([start]), {start}, {}

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
            for other_con in by_device.get(dev, []):
                nxt = (dev, other_con)
                if nxt not in seen:
                    seen.add(nxt)
                    prev[nxt] = cur
                    q.append(nxt)

        if start != goal and goal not in prev:
            return [], [], []

        # reconstruct path
        path = [goal]
        while path[-1] != start:
            path.append(prev[path[-1]])
        path.reverse()

        # -------------------------------------------------------------
        # build disconnect chain, net chain, and connector chain
        chain, net_chain, connector_chain = [], [], []

        for a, b in zip(path, path[1:]):
            net_a = net_of.get(a)

            # collect unique net chain
            if net_a and (not net_chain or net_chain[-1] != net_a):
                net_chain.append(net_a)

            # detect disconnect traversal
            if a[0] == b[0] and a[0] in is_disconnect:
                dev = a[0]
                port_a, port_b = a[1], b[1]
                chain.append(f"{dev}({port_a},{port_b})")

        # build connector chain (each item: net.connector)
        for dev, con in path:
            net = net_of.get((dev, con))
            if net:
                connector_chain.append(f"{net}.{dev}{con}")
            else:
                # still include device.connector even if net missing
                connector_chain.append(f"?.{dev}{con}")

        return chain, net_chain, connector_chain

    # -------------------------------------------------------------
    # apply to each channel pair
    for row in channel_map:
        from_key = (row.get("from_device_refdes"), row.get("from_device_channel_id"))
        to_key = (row.get("to_device_refdes"), row.get("to_device_channel_id"))
        if not all(from_key) or not all(to_key):
            continue

        from_cn = (from_key[0], connector_of_channel(from_key))
        to_cn = (to_key[0], connector_of_channel(to_key))

        n_from = net_of.get(from_cn)
        n_to = net_of.get(to_cn)

        if n_from and n_to and n_from == n_to:
            row["disconnect_refdes_requirement"] = ""
            row["chain_of_nets"] = n_from
            row["chain_of_connectors"] = (
                f"{n_from}.{from_cn[0]}{from_cn[1]};{n_to}.{to_cn[0]}{to_cn[1]}"
            )
            continue

        chain, net_chain, connector_chain = _shortest_disconnect_chain(from_cn, to_cn)
        if chain or net_chain or connector_chain:
            row["disconnect_refdes_requirement"] = ";".join(chain)
            row["chain_of_nets"] = ";".join(net_chain)
            row["chain_of_connectors"] = ";".join(connector_chain)

    with open(fileio.path("channel map"), "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=channel_map[0].keys(), delimiter="\t")
        writer.writeheader()
        writer.writerows(channel_map)


def make_instances_from_bom():
    """
    Creates instances for all devices and disconnects from the BOM.

    Reads the Bill of Materials (BOM) and imports each device or disconnect into the
    instances list using `library_utils.pull()`. Each item is imported with its manufacturer,
    part number, revision, and library information.

    Items with the `"disconnect"` field set are imported as type `"disconnect"`,
    all others are imported as type `"device"`.
    """
    for device in fileio.read_tsv("bom"):
        if device.get("disconnect"):
            item_type = "disconnect"
        else:
            item_type = "device"

        library_utils.pull(
            {
                "instance_name": device.get("device_refdes"),
                "mfg": device.get("MFG"),
                "mpn": device.get("MPN"),
                "item_type": item_type,
                "lib_repo": device.get("lib_repo"),
                "lib_subpath": device.get("lib_subpath"),
                "lib_rev_used_here": device.get("rev"),
            }
        )
