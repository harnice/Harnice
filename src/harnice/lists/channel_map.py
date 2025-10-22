import csv
import os
from harnice import fileio

COLUMNS = [
    "merged_net",
    "from_device_refdes",
    "from_device_channel_id",
    "from_channel_type",
    "to_device_refdes",
    "to_device_channel_id",
    "to_channel_type",
    "multi_ch_junction_id",
    "disconnect_refdes_requirement",
    "chain_of_nets",
    "manual_map_channel_python_equiv",
]


def new():
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
            sig_channel = signal.get("channel_id")

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

    return channel_map


def map(from_key, to_key=None, multi_ch_junction_key=""):
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
            from_channel["to_channel_type"] = to_channel.get("from_channel_type")
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
        writer = csv.DictWriter(f, fieldnames=COLUMNS, delimiter="\t")
        writer.writeheader()
        writer.writerows(updated_channels)
