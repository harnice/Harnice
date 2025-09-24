import csv
from harnice import fileio, system_utils


def find_disconnects_between(from_cn_key, to_cn_key, connector_list):
    """
    Returns a list of device_refdes marked as disconnects that lie between
    from_cn_key and to_cn_key, based on shared nets.
    """
    visited_nets = set()
    disconnects_found = []

    def dfs(current_cn_key, target_cn_key):
        nonlocal disconnects_found

        # Get the net for the current connector
        net = None
        for row in connector_list:
            if (
                row.get("device_refdes") == current_cn_key[0]
                and row.get("connector") == current_cn_key[1]
            ):
                net = row.get("net")
                break
        if not net:
            return False

        if net in visited_nets:
            return False
        visited_nets.add(net)

        # Record disconnects on this net
        for row in connector_list:
            if row.get("net") == net and row.get("disconnect") == "TRUE":
                disconnects_found.append(row.get("device_refdes"))

        # If the target connector is also on this net, stop
        for row in connector_list:
            if (
                row.get("device_refdes") == target_cn_key[0]
                and row.get("connector") == target_cn_key[1]
                and row.get("net") == net
            ):
                return True

        # Otherwise, keep exploring connected connectors
        for row in connector_list:
            if row.get("net") == net:
                next_cn_key = (row.get("device_refdes"), row.get("connector"))
                if dfs(next_cn_key, target_cn_key):
                    return True

        return False

    dfs(from_cn_key, to_cn_key)
    return disconnects_found


# ---------------- Main Script ----------------

with open(fileio.path("channel map"), newline="", encoding="utf-8") as f:
    channel_map = list(csv.DictReader(f, delimiter="\t"))

with open(fileio.path("system connector list"), newline="", encoding="utf-8") as f:
    connector_list = list(csv.DictReader(f, delimiter="\t"))

for channel in channel_map:
    from_ch_key = (
        channel.get("from_device_refdes"),
        channel.get("from_device_channel_id"),
    )
    from_cn_key = (
        channel.get("from_device_refdes"),
        system_utils.connector_of_channel(from_ch_key),
    )
    to_ch_key = (
        channel.get("to_device_refdes"),
        channel.get("to_device_channel_id"),
    )
    if to_ch_key == (None, None) or to_ch_key == ("",""):
        continue
    to_cn_key = (
        channel.get("to_device_refdes"),
        system_utils.connector_of_channel(to_ch_key),
    )

    from_net, to_net = None, None
    for cn_key in connector_list:
        if cn_key.get("device_refdes") == from_cn_key[0] and cn_key.get("connector") == from_cn_key[1]:
            from_net = cn_key.get("net")
        if cn_key.get("device_refdes") == to_cn_key[0] and cn_key.get("connector") == to_cn_key[1]:
            to_net = cn_key.get("net")

    if not from_net or from_net != to_net:
        # Try to trace disconnects recursively
        disconnects = find_disconnects_between(from_cn_key, to_cn_key, connector_list)
        if disconnects:
            channel["disconnect_refdes_key"] = str(disconnects)

# Write updated channel map back
with open(fileio.path("channel map"), "w", newline="", encoding="utf-8") as f:
    fieldnames = channel_map[0].keys()
    writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")
    writer.writeheader()
    writer.writerows(channel_map)
