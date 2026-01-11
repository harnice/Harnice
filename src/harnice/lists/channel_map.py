import csv
import os
from harnice import fileio

COLUMNS = [
    "merged_net", #documentation needed
    "from_device_refdes", #documentation needed
    "from_device_channel_id", #documentation needed
    "from_channel_type", #documentation needed
    "to_device_refdes", #documentation needed
    "to_device_channel_id", #documentation needed
    "to_channel_type", #documentation needed
    "multi_ch_junction_id", #documentation needed
    "disconnect_refdes_requirement", #documentation needed
    "chain_of_connectors", #documentation needed
    "chain_of_nets", #documentation needed
    "manual_map_channel_python_equiv", #documentation needed
]


def new():
    """
    Makes a new blank channel map. Overwrites existing channel map.

    Args: none

    Returns: none
    """
    channel_map = []

    for connector in fileio.read_tsv("system connector list"):
        device_refdes = connector.get("device_refdes")

        if connector.get("disconnect") == "TRUE":
            continue

        device_signals_list_path = os.path.join(
            fileio.dirpath("instance_data"),
            "device",
            device_refdes,
            f"{device_refdes}-signals_list.tsv",
        )

        for signal in fileio.read_tsv(device_signals_list_path):
            sig_channel = signal.get("channel_id")

            already = any(
                row.get("from_device_refdes") == device_refdes
                and row.get("from_device_channel_id") == sig_channel
                for row in channel_map
            )
            if already:
                continue

            if not signal.get("connector_name") == connector.get("connector"):
                continue

            channel_map_row = {
                "merged_net": connector.get("merged_net", ""),
                "from_channel_type": signal.get("channel_type", ""),
                "from_device_refdes": device_refdes,
                "from_device_channel_id": sig_channel,
            }
            channel_map.append(channel_map_row)

    # write channel map TSV
    with open(fileio.path("channel map"), "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS, delimiter="\t")
        writer.writeheader()
        writer.writerows(channel_map)

    # initialize mapped channels set TSV (empty, single column)
    with open(
        fileio.path("mapped channels set"), "w", newline="", encoding="utf-8"
    ) as f:
        pass

    return channel_map


def map(from_key, to_key=None, multi_ch_junction_key=""):
    if from_key in already_mapped_set():
        raise ValueError(f"from_key {from_key} already mapped")
    if to_key and to_key in already_mapped_set():
        raise ValueError(f"to_key {to_key} already mapped")

    channels = fileio.read_tsv("channel map")

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

    if not to_channel and multi_ch_junction_key == "":
        raise ValueError(f"to_key {to_key} not found in channel map")
    else:
        require_to = bool(to_key[0] or to_key[1])

    updated_channels, found_from, found_to = [], False, False

    for from_channel in channels:
        if (
            from_channel.get("from_device_refdes") == from_key[0]
            and from_channel.get("from_device_channel_id") == from_key[1]
        ):
            from_channel["to_device_refdes"] = to_key[0]
            from_channel["to_device_channel_id"] = to_key[1]
            from_channel["to_channel_type"] = to_channel.get("from_channel_type")
            if multi_ch_junction_key:
                from_channel["multi_ch_junction_id"] = multi_ch_junction_key
            found_from = True

            if require_to:
                from_channel["manual_map_channel_python_equiv"] = (
                    f"channel_map.map({from_key}, {to_key})"
                )
            elif multi_ch_junction_key:
                from_channel["manual_map_channel_python_equiv"] = (
                    f"channel_map.map({from_key}, multi_ch_junction_key={multi_ch_junction_key})"
                )
        elif (
            require_to
            and from_channel.get("from_device_refdes") == to_key[0]
            and from_channel.get("from_device_channel_id") == to_key[1]
        ):
            found_to = True
            continue
        updated_channels.append(from_channel)

    if not found_from:
        raise ValueError(f"from_key {from_key} not found in channel map")
    if require_to and not found_to:
        raise ValueError(f"to_key {to_key} not found in channel map")

    already_mapped_set_append(from_key)
    already_mapped_set_append(to_key)

    with open(fileio.path("channel map"), "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS, delimiter="\t")
        writer.writeheader()
        writer.writerows(updated_channels)


def already_mapped_set_append(key):
    items = already_mapped_set()
    if str(key) in items:
        raise ValueError(f"key {key} already mapped")
    items.add(str(key))
    with open(
        fileio.path("mapped channels set"), "w", newline="", encoding="utf-8"
    ) as f:
        writer = csv.writer(f, delimiter="\t")
        for item in sorted(items):
            writer.writerow([item])


def already_mapped_set():
    if not os.path.exists(fileio.path("mapped channels set")):
        return set()
    with open(fileio.path("mapped channels set"), newline="", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t")
        return set(row[0] for row in reader if row)


def already_mapped(key):
    if str(key) in already_mapped_set():
        return True
    else:
        return False
