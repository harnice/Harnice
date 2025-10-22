import os
import csv
from harnice import fileio, component_library


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
