import os
import csv
from harnice import fileio

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
                fileio.dirpath("instance_data"),
                "disconnect",
                item.get("device_refdes"),
                f"{item.get('device_refdes')}-signals_list.tsv",
            )

            available_disconnect_channels = set()
            for signal in fileio.read_tsv(disconnect_signals_list_path):
                if signal.get("channel_id") in available_disconnect_channels:
                    continue
                available_disconnect_channels.add(signal.get("channel_id"))

                disconnect_map_rows.append(
                    {
                        "disconnect_refdes": item.get("device_refdes"),
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
        fileio.path("mapped A-side channels through disconnects set"),
        "w",
        newline="",
        encoding="utf-8",
    ) as f:
        pass


def assign(a_side_key, disconnect_key):
    # a_side is the (device refdes, channel_id) that is on the A-side of the disconnect
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

    already_assigned_channels_through_disconnects_set_append(
        a_side_key, disconnect_key[0]
    )
    already_assigned_disconnects_set_append(disconnect_key)

    with open(fileio.path("disconnect map"), "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS, delimiter="\t")
        writer.writeheader()
        writer.writerows(updated_channels)


def already_assigned_channels_through_disconnects_set_append(key, disconnect_refdes):
    item = f"{key}:{disconnect_refdes}"
    items = set(already_assigned_channels_through_disconnects_set())
    if item in items:
        raise ValueError(
            f"channel {key} through disconnect {disconnect_refdes} already assigned"
        )
    with open(
        fileio.path("mapped A-side channels through disconnects set"),
        "a",
        newline="",
        encoding="utf-8",
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
    with open(
        fileio.path("mapped A-side channels through disconnects set"),
        newline="",
        encoding="utf-8",
    ) as f:
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


def channel_is_already_assigned_through_disconnect(key, disconnect_refdes):
    if (
        f"{str(key)}:{disconnect_refdes}"
        in already_assigned_channels_through_disconnects_set()
    ):
        return True
    else:
        return False


def disconnect_is_already_assigned(key):
    if str(key) in already_assigned_disconnects_set():
        return True
    else:
        return False

def ensure_requirements_met():
    for row in fileio.read_tsv("disconnect map"):
        if row.get("A-side_device_refdes") not in [None, ""] and row.get("disconnect_channel_id") in [None, ""]:
            raise ValueError(f"Channel '{row.get('A-side_device_refdes')}.{row.get('A-side_device_channel_id')}' to '{row.get('B-side_device_refdes')}.{row.get('B-side_device_channel_id')}' could not find a compatible disconnect channel through '{row.get('disconnect_refdes')}'")