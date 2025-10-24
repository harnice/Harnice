import os
import csv
from harnice import fileio
from harnice.lists import signals_list
from harnice.products import chtype

COLUMNS = [
    "net",
    "circuit_id",
    "signal",
    "net_from_refdes",
    "net_from_channel_id",
    "net_from_connector_name",
    "net_from_cavity",
    "net_to_refdes",
    "net_to_channel_id",
    "net_to_connector_name",
    "net_to_cavity",
    "from_side_device_refdes",
    "from_side_device_chname",
    "to_side_device_refdes",
    "to_side_device_chname",
    "from_channel_type",
    "to_channel_type",
]


def new():
    # --- helper: first non-empty field ---
    def first_nonempty(row, *candidate_names):
        for name in candidate_names:
            value = (row.get(name) or "").strip()
            if value:
                return value
        return ""

    # --- load disconnect map and build index ---
    disconnect_index = {}

    for row in fileio.read_tsv("disconnect map"):
        a_refdes = first_nonempty(
            row,
            "A-side_device_refdes",
            "from_destination_device_refdes",
            "from_device_refdes",
        )
        if not a_refdes:
            continue  # skip "available channel" rows

        a_channel_id = first_nonempty(
            row,
            "A-side_device_channel_id",
            "from_destination_device_channel_id",
            "from_device_channel_id",
        )
        b_refdes = first_nonempty(
            row,
            "B-side_device_refdes",
            "to_destination_device_refdes",
            "to_device_refdes",
        )
        b_channel_id = first_nonempty(
            row,
            "B-side_device_channel_id",
            "to_destination_device_channel_id",
            "to_device_channel_id",
        )

        disconnect_refdes = first_nonempty(row, "disconnect_refdes")
        disconnect_channel_id = first_nonempty(
            row, "disconnect_channel_id", "disconnect_channel_id"
        )

        key_forward = (
            a_refdes,
            a_channel_id,
            b_refdes,
            b_channel_id,
            disconnect_refdes,
        )
        key_reverse = (
            b_refdes,
            b_channel_id,
            a_refdes,
            a_channel_id,
            disconnect_refdes,
        )

        disconnect_index[key_forward] = disconnect_channel_id
        disconnect_index[key_reverse] = disconnect_channel_id

    circuits_list = []
    circuit_id = 0

    # --- resolvers ---
    def resolve_device_endpoint(refdes, channel_id, signal):
        device_signals_list_path = os.path.join(
            fileio.dirpath("imported_instances"),
            "device",
            refdes,
            f"{refdes}-signals_list.tsv"
        )
        connector_name = (
            signals_list.connector_name_of_channel(channel_id, device_signals_list_path)
            if channel_id
            else ""
        )
        cavity = (
            signals_list.cavity_of_signal(channel_id, signal, device_signals_list_path)
            if channel_id
            else ""
        )
        return {
            "refdes": refdes,
            "channel_id": channel_id,
            "connector_name": connector_name,
            "cavity": cavity,
        }

    def resolve_disconnect_endpoint(refdes, side, signal, channel_id):
        disconnect_signals_list_path = os.path.join(
            fileio.dirpath("disconnects"), refdes, f"{refdes}-signals_list.tsv"
        )

        row = None
        for disconnect_signal_row in fileio.read_tsv(disconnect_signals_list_path):
            if disconnect_signal_row.get("signal", "").strip() == signal.strip():
                if (
                    disconnect_signal_row.get("channel_id", "").strip()
                    == channel_id.strip()
                ):
                    row = disconnect_signal_row
                    break

        if row is None:
            raise ValueError(
                f"Signal {signal} of channel {channel_id} not found in {disconnect_signals_list_path}"
            )

        cavity = (row.get(f"{side}_cavity") or "").strip()
        return {
            "refdes": refdes,
            "channel_id": channel_id,
            "connector_name": side,
            "cavity": cavity,
        }

    # --- iterate channel map rows ---
    for row in fileio.read_tsv("channel map"):
        if not row.get("from_device_channel_id"):
            continue
        if not row.get("to_device_refdes") and not row.get("multi_ch_junction_id"):
            continue

        from_refdes = row["from_device_refdes"].strip()
        from_channel_id = row["from_device_channel_id"].strip()
        to_refdes = row["to_device_refdes"].strip()
        to_channel_id = row["to_device_channel_id"].strip()

        signals = chtype.signals(row.get("from_channel_type"))

        # --- parse disconnect requirement ---
        disconnect_chain = []
        if row.get("disconnect_refdes_requirement"):
            for token in row["disconnect_refdes_requirement"].split(";"):
                token = token.strip()
                if token:
                    refdes, sides = token.split("(", 1)
                    refdes = refdes.strip()
                    sides = sides.rstrip(")")
                    side_from, side_to = [s.strip() for s in sides.split(",")]
                    disconnect_chain.append((refdes, side_from, side_to))
        disconnect_set = {d[0] for d in disconnect_chain}

        # --- nets list ---
        nets = [n.strip() for n in row.get("chain_of_nets", "").split(";") if n.strip()]

        # --- connection steps (disconnects + final device) ---
        connection_steps = disconnect_chain + [(to_refdes, None, None)]

        if len(connection_steps) != len(nets):
            step_labels = [s[0] for s in connection_steps]
            raise ValueError(
                f"While building circuits from channel_id '{from_channel_id}' of device '{from_refdes}' "
                f"to channel_id '{to_channel_id}' of device '{to_refdes}', "
                f"found {len(connection_steps)} connection steps: "
                f"{', '.join(step_labels) or 'none'}, "
                f"but expected {len(nets)} because there are {len(nets)} nets "
                f"from channel end '{from_channel_id}' to channel end '{to_channel_id}' "
                f"({'; '.join(nets) or 'no nets listed'}). "
                "Each net should correspond to one physical connection segment between devices or disconnects. "
                "Check the channel map for missing or unexpected info in cells, or if the disconnect requirements match the disconnect map."
            )

        # --- iterate signals ---
        for signal in signals:
            current_refdes = from_refdes
            current_side = None
            current_channel_id = from_channel_id

            for step, net in zip(connection_steps, nets):
                refdes, side_from, side_to = step

                if side_from is not None:
                    # disconnect step
                    disconnect_key = (
                        from_refdes,
                        from_channel_id,
                        to_refdes,
                        to_channel_id,
                        refdes,
                    )
                    mapped_channel_id = disconnect_index[disconnect_key]

                    if current_refdes in disconnect_set:
                        left = resolve_disconnect_endpoint(
                            current_refdes, current_side, signal, current_channel_id
                        )
                    else:
                        left = resolve_device_endpoint(
                            current_refdes, current_channel_id, signal
                        )

                    right = resolve_disconnect_endpoint(
                        refdes, side_from, signal, mapped_channel_id
                    )

                    circuits_list.append(
                        {
                            "net": net,
                            "circuit_id": circuit_id,
                            "from_channel_type": row.get("from_channel_type"),
                            "to_channel_type": row.get("to_channel_type"),
                            "signal": signal,
                            "net_from_refdes": left["refdes"],
                            "net_from_channel_id": left["channel_id"],
                            "net_from_connector_name": left["connector_name"],
                            "net_from_cavity": left["cavity"],
                            "net_to_refdes": right["refdes"],
                            "net_to_channel_id": right["channel_id"],
                            "net_to_connector_name": right["connector_name"],
                            "net_to_cavity": right["cavity"],
                            "from_side_device_refdes": from_refdes,
                            "from_side_device_chname": from_channel_id,
                            "to_side_device_refdes": to_refdes,
                            "to_side_device_chname": to_channel_id,
                        }
                    )
                    circuit_id += 1

                    current_refdes = refdes
                    current_side = side_to
                    current_channel_id = mapped_channel_id

                else:
                    # final device step
                    if current_refdes in disconnect_set:
                        left = resolve_disconnect_endpoint(
                            current_refdes, current_side, signal, current_channel_id
                        )
                    else:
                        left = resolve_device_endpoint(
                            current_refdes, current_channel_id, signal
                        )

                    right = resolve_device_endpoint(refdes, to_channel_id, signal)

                    circuits_list.append(
                        {
                            "net": net,
                            "circuit_id": circuit_id,
                            "signal": signal,
                            "from_channel_type": row.get("from_channel_type"),
                            "to_channel_type": row.get("to_channel_type"),
                            "net_from_refdes": left["refdes"],
                            "net_from_channel_id": left["channel_id"],
                            "net_from_connector_name": left["connector_name"],
                            "net_from_cavity": left["cavity"],
                            "net_to_refdes": right["refdes"],
                            "net_to_channel_id": right["channel_id"],
                            "net_to_connector_name": right["connector_name"],
                            "net_to_cavity": right["cavity"],
                            "from_side_device_refdes": from_refdes,
                            "from_side_device_chname": from_channel_id,
                            "to_side_device_refdes": to_refdes,
                            "to_side_device_chname": to_channel_id,
                        }
                    )
                    circuit_id += 1

    # --- write circuits list ---
    with open(fileio.path("circuits list"), "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS, delimiter="\t")
        writer.writeheader()
        writer.writerows(circuits_list)
