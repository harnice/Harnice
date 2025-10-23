import os
from harnice import fileio
from harnice.utils import library_utils
from harnice.lists import instances_list


def pull_devices_from_library():
    imported_devices = []
    for refdes in fileio.read_tsv("bom"):
        if refdes not in imported_devices:
            if refdes.get("disconnect") == "TRUE":
                if refdes.get("MPN") in [None, ""]:
                    raise ValueError(
                        f"MPN is required to be able to import disconnect {refdes['device_ref_des']}"
                    )
                if refdes.get("lib_repo") in [None, ""]:
                    raise ValueError(
                        f"lib_repo is required to be able to import disconnect {refdes['device_ref_des']}"
                    )
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
                    library_utils.pull_item_from_library(
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
                library_utils.pull_item_from_library(
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


def mpn_of_device_refdes(refdes):
    for row in fileio.read_tsv("bom"):
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
    for row in fileio.read_tsv(device_signals_list_path):
        if row.get("channel_id", "").strip() == channel_id.strip():
            return row.get("connector_name", "").strip()

    raise ValueError(f"Connector not found for channel {key}")


def disconnects_in_net(net):
    disconnects = []
    for connector in fileio.read_tsv("system connector list"):
        if connector.get("net") == net:
            if connector.get("disconnect") == "TRUE":
                disconnects.append(connector.get("device_refdes"))
    return disconnects


def find_connector_with_no_circuit(connector_list, circuits_list):
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
                f"Connector '{connector_name}' of device '{device_refdes}' does not contain any circuits"
            )

def make_instances_for_connectors_cavities_nodes_channels_circuits():
    connectors_list = fileio.read_tsv("system connector list")

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
                "item_type": "Node",
                "location_type": "Node",
                "connector_group": from_connector_key,
            },
            ignore_duplicates=True,
        )

        # from connector
        instances_list.new_instance(
            f"{from_connector_key}.conn",
            {
                "net": circuit.get("net"),
                "item_type": "Connector",
                "location_type": "Node",
                "connector_group": from_connector_key,
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
                "item_type": "Connector cavity",
                "parent_instance": f"{from_connector_key}.conn",  # from connector instance
                "location_type": "Node",
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
                "item_type": "Node",
                "location_type": "Node",
                "connector_group": to_connector_key,
            },
            ignore_duplicates=True,
        )

        # to connector
        instances_list.new_instance(
            f"{to_connector_key}.conn",
            {
                "net": circuit.get("net"),
                "item_type": "Connector",
                "location_type": "Node",
                "connector_group": to_connector_key,
                "this_instance_mating_device_refdes": circuit.get("net_from_refdes"),
                "this_instance_mating_device_connector": circuit.get(
                    "net_from_connector_name"
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
                "item_type": "Connector cavity",
                "parent_instance": f"{to_connector_key}.conn",  # to connector instance
                "location_type": "Node",
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
                "item_type": "Circuit",
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

        # add channel
        instances_list.new_instance(
            f"channel-{circuit.get('from_side_device_refdes')}.{circuit.get('from_side_device_chname')}-{circuit.get('to_side_device_refdes')}.{circuit.get('to_side_device_chname')}",
            {
                "net": circuit.get("net"),
                "item_type": "Channel",
                "channel_group": f"channel-{circuit.get('from_side_device_refdes')}.{circuit.get('from_side_device_chname')}-{circuit.get('to_side_device_refdes')}.{circuit.get('to_side_device_chname')}",
                "location_type": "Segment",
                "node_at_end_a": f"{circuit.get('net_from_refdes')}.{circuit.get('net_from_connector_name')}.conn",
                "node_at_end_b": f"{circuit.get('net_to_refdes')}.{circuit.get('net_to_connector_name')}.conn",
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

    for connector in fileio.read_tsv("system connector list"):
        try:
            instances_list.modify(
                f"{connector.get('device_refdes')}.{connector.get('connector')}.conn",
                {
                    "mating_device_refdes": connector.get("device_refdes"),
                    "mating_device_connector": connector.get("connector"),
                    "mating_device_connector_mpn": connector.get("connector_mpn"),
                },
            )
        except ValueError:
            pass
