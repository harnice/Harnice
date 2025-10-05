import csv
from harnice import fileio, icd, system_utils

verbose = True
extra_verbose = False

def disconnect_channel_map():
    """Always reloads the disconnect channel map from TSV."""
    with open(fileio.path("disconnect channel map"), newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter="\t"))

for required_channel in disconnect_channel_map():

    # skip available channel rows (A-side empty)
    if required_channel.get("A-side_device_refdes") in [None, ""]:
        continue

    disconnect_refdes = required_channel.get("disconnect_refdes")

    # collect available candidates for the same disconnect_refdes
    available_candidates = [
        c for c in disconnect_channel_map()
        if c.get("A-side_device_refdes") in [None, ""]
        and c.get("disconnect_refdes") == disconnect_refdes
    ]

    required_ch_attributes = {
        "A-side_device_channel_type_id": required_channel.get("A-side_device_channel_type_id"),
        "A-side_device_compatible_channel_type_ids": required_channel.get("A-side_device_compatible_channel_type_ids"),
        "B-side_device_channel_type_id": required_channel.get("B-side_device_channel_type_id"),
        "B-side_device_compatible_channel_type_ids": required_channel.get("B-side_device_compatible_channel_type_ids"),
    }

    # dict keyed by disconnect_channel_id only
    candidate_ch_attributes = {}
    for c in available_candidates:
        channel_id = c.get("disconnect_channel_id")
        candidate_ch_attributes[channel_id] = {
            "A-port_channel_type": c.get("A-port_channel_type"),
            "A-port_compatible_channel_type_ids": c.get("A-port_compatible_channel_type_ids"),
            "B-port_channel_type": c.get("B-port_channel_type"),
            "B-port_compatible_channel_type_ids": c.get("B-port_compatible_channel_type_ids"),
        }

    # decide what to map
    map_mode = 0
    map_message = None

    if verbose:
        print(f"\nLooking for a map for {required_channel.get('A-side_device_refdes')}.{required_channel.get('A-side_device_channel_id')} -> {required_channel.get('B-side_device_refdes')}.{required_channel.get('B-side_device_channel_id')} inside disconnect {disconnect_refdes}")

    for candidate in available_candidates:
        if extra_verbose:
            print(f"     Checking candidate {candidate.get('disconnect_channel_id')} of {candidate.get('disconnect_refdes')}")

        if required_ch_attributes.get("A-side_device_channel_type_id") == candidate.get("B-port_channel_type"):
            map_mode = 1
            map_message = "Channel type of A-side device matches channel type of B-port of disconnect"
            break

        if extra_verbose:
            print(f"          Channel type of A-side device {required_ch_attributes.get('A-side_device_channel_type_id')} does not match channel type of B-port of disconnect {candidate.get('B-port_channel_type')}")

        if required_ch_attributes.get("B-side_device_channel_type_id") == candidate.get("A-port_channel_type"):
            map_mode = 2
            map_message = "Channel type of B-side device matches channel type of A-port of disconnect"
            break

        if extra_verbose:
            print(f"          Channel type of B-side device {required_ch_attributes.get('B-side_device_channel_type_id')} does not match channel type of A-port of disconnect {candidate.get('A-port_channel_type')}")

        if required_ch_attributes.get("A-side_device_channel_type_id") in icd.compatible_channel_types(candidate.get("B-port_channel_type")):
            map_mode = 3
            map_message = "Channel type of A-side device is found in compatibles of channel type of B-port of disconnect"
            break

        if extra_verbose:
            print(f"          Channel type of A-side device {required_ch_attributes.get('A-side_device_channel_type_id')} is not found in compatibles of channel type of B-port of disconnect {icd.compatible_channel_types(candidate.get('B-port_channel_type'))}")

        if required_ch_attributes.get("B-side_device_channel_type_id") in icd.compatible_channel_types(candidate.get("A-port_channel_type")):
            map_mode = 4
            map_message = "Channel type of B-side device is found in compatibles of channel type of A-port of disconnect"
            break

        if extra_verbose:
            print(f"          Channel type of B-side device {required_ch_attributes.get('B-side_device_channel_type_id')} is not found in compatibles of channel type of A-port of disconnect {icd.compatible_channel_types(candidate.get('A-port_channel_type'))}")

        if candidate.get("A-port_channel_type") in icd.compatible_channel_types(required_ch_attributes.get("B-side_device_channel_type_id")):
            map_mode = 5
            map_message = "Channel type of A-port of disconnect is found in compatibles of channel type of B-side device"
            break

        if extra_verbose:
            print(f"          Channel type of A-port of disconnect {candidate.get('A-port_channel_type')} is not found in compatibles of channel type of B-side device {icd.compatible_channel_types(required_ch_attributes.get('B-side_device_channel_type_id'))}")

        if candidate.get("B-port_channel_type") in icd.compatible_channel_types(required_ch_attributes.get("A-side_device_channel_type_id")):
            map_mode = 6
            map_message = "Channel type of B-port of disconnect is found in compatibles of channel type of A-side device"
            break

        if extra_verbose:
            print(f"          Channel type of B-port of disconnect {candidate.get('B-port_channel_type')} is not found in compatibles of channel type of A-side device {icd.compatible_channel_types(required_ch_attributes.get('A-side_device_channel_type_id'))}")

    if map_mode == 0:
        print(f"ERROR: No compatible channel found for {required_channel.get('A-side_device_refdes')}.{required_channel.get('A-side_device_channel_id')} -> {required_channel.get('B-side_device_refdes')}.{required_channel.get('B-side_device_channel_id')}")
    
    else:
        a_side_key = (required_channel.get("A-side_device_refdes"), required_channel.get("A-side_device_channel_id"))
        disconnect_key = (candidate.get("disconnect_refdes"), candidate.get("disconnect_channel_id"))
        system_utils.map_channel_to_disconnect_channel(a_side_key, disconnect_key)

        if verbose:
            print(f"Mapped to {candidate.get('disconnect_channel_id')} of {candidate.get('disconnect_refdes')} because: ({map_message})")