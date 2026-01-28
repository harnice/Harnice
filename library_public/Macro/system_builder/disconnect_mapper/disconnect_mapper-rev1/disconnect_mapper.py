from harnice import fileio
from harnice.lists import disconnect_map
from harnice.products import chtype

verbose = False
extra_verbose = False

for required_channel in fileio.read_tsv("disconnect map"):
    # skip available channel rows (A-side empty)
    if required_channel.get("A-side_device_refdes") in [None, ""]:
        continue

    # Don't map a channel if the disconnect channel has already been mapped
    disconnect_refdes = required_channel.get("disconnect_refdes")
    disconnect_channel_id = required_channel.get("disconnect_channel_id")
    a_side_channel_key = (
        required_channel.get("A-side_device_refdes"),
        required_channel.get("A-side_device_channel_id"),
    )

    if disconnect_map.channel_is_already_assigned_through_disconnect(
        a_side_channel_key, disconnect_refdes
    ):
        if verbose:
            print(
                f"Skipping channel {a_side_channel_key} through disconnect {disconnect_refdes} - already assigned"
            )
        continue

    # collect available candidates for the same disconnect_refdes
    available_candidates = [
        c
        for c in fileio.read_tsv("disconnect map")
        if c.get("A-side_device_refdes") in [None, ""]
        and c.get("disconnect_refdes") == disconnect_refdes
    ]

    required_ch_attributes = {
        "A-side_device_channel_type": required_channel.get(
            "A-side_device_channel_type"
        ),
        "B-side_device_channel_type": required_channel.get(
            "B-side_device_channel_type"
        ),
    }

    # dict keyed by disconnect_channel_id only
    candidate_ch_attributes = {}
    for candidate in available_candidates:
        channel_id = candidate.get("disconnect_channel_id")
        candidate_ch_attributes[channel_id] = {
            "A-port_channel_type": candidate.get("A-port_channel_type"),
            "B-port_channel_type": candidate.get("B-port_channel_type"),
        }

    # decide what to map
    map_mode = 0
    map_message = None

    if verbose:
        print(
            f"\nLooking for a map for {required_channel.get('A-side_device_refdes')}.{required_channel.get('A-side_device_channel_id')} -> {required_channel.get('B-side_device_refdes')}.{required_channel.get('B-side_device_channel_id')} inside disconnect {disconnect_refdes}"
        )

    for candidate in available_candidates:
        if disconnect_map.disconnect_is_already_assigned(
            (candidate.get("disconnect_refdes"), candidate.get("disconnect_channel_id"))
        ):
            if verbose:
                print(
                    f"Skipping candidate {candidate.get('disconnect_channel_id')} of {candidate.get('disconnect_refdes')} - already assigned"
                )
            continue

        if extra_verbose:
            print(
                f"     Checking candidate {candidate.get('disconnect_channel_id')} of {candidate.get('disconnect_refdes')}"
            )

        if required_ch_attributes.get("A-side_device_channel_type") == candidate.get(
            "B-port_channel_type"
        ):
            map_mode = 1
            map_message = "Channel type of A-side device matches channel type of B-port of disconnect"
            break

        if extra_verbose:
            print(
                f"          Channel type of A-side device {required_ch_attributes.get('A-side_device_channel_type')} does not match channel type of B-port of disconnect {candidate.get('B-port_channel_type')}"
            )

        if required_ch_attributes.get("B-side_device_channel_type") == candidate.get(
            "A-port_channel_type"
        ):
            map_mode = 2
            map_message = "Channel type of B-side device matches channel type of A-port of disconnect"
            break

        if extra_verbose:
            print(
                f"          Channel type of B-side device {required_ch_attributes.get('B-side_device_channel_type')} does not match channel type of A-port of disconnect {candidate.get('A-port_channel_type')}"
            )

        if required_ch_attributes.get(
            "A-side_device_channel_type"
        ) in chtype.compatibles(candidate.get("B-port_channel_type")):
            map_mode = 3
            map_message = "Channel type of A-side device is found in compatibles of channel type of B-port of disconnect"
            break

        if extra_verbose:
            print(
                f"          Channel type of A-side device {required_ch_attributes.get('A-side_device_channel_type')} is not found in compatibles of channel type of B-port of disconnect {chtype.compatibles(candidate.get('B-port_channel_type'))}"
            )

        if required_ch_attributes.get(
            "B-side_device_channel_type"
        ) in chtype.compatibles(candidate.get("A-port_channel_type")):
            map_mode = 4
            map_message = "Channel type of B-side device is found in compatibles of channel type of A-port of disconnect"
            break

        if extra_verbose:
            print(
                f"          Channel type of B-side device {required_ch_attributes.get('B-side_device_channel_type')} is not found in compatibles of channel type of A-port of disconnect {chtype.compatibles(candidate.get('A-port_channel_type'))}"
            )

        if candidate.get("A-port_channel_type") in chtype.compatibles(
            required_ch_attributes.get("B-side_device_channel_type")
        ):
            map_mode = 5
            map_message = "Channel type of A-port of disconnect is found in compatibles of channel type of B-side device"
            break

        if extra_verbose:
            print(
                f"          Channel type of A-port of disconnect {candidate.get('A-port_channel_type')} is not found in compatibles of channel type of B-side device {chtype.compatibles(required_ch_attributes.get('B-side_device_channel_type'))}"
            )

        if candidate.get("B-port_channel_type") in chtype.compatibles(
            required_ch_attributes.get("A-side_device_channel_type")
        ):
            map_mode = 6
            map_message = "Channel type of B-port of disconnect is found in compatibles of channel type of A-side device"
            break

        if extra_verbose:
            print(
                f"          Channel type of B-port of disconnect {candidate.get('B-port_channel_type')} is not found in compatibles of channel type of A-side device {chtype.compatibles(required_ch_attributes.get('A-side_device_channel_type'))}"
            )

    if map_mode == 0:
        print(
            f"ERROR: No compatible channel found for {required_channel.get('A-side_device_refdes')}.{required_channel.get('A-side_device_channel_id')} -> {required_channel.get('B-side_device_refdes')}.{required_channel.get('B-side_device_channel_id')}"
        )

    else:
        a_side_key = (
            required_channel.get("A-side_device_refdes"),
            required_channel.get("A-side_device_channel_id"),
        )
        disconnect_key = (
            candidate.get("disconnect_refdes"),
            candidate.get("disconnect_channel_id"),
        )
        disconnect_map.assign(a_side_key, disconnect_key)

        if verbose:
            print(
                f"Mapped to {candidate.get('disconnect_channel_id')} of {candidate.get('disconnect_refdes')} because: ({map_message})"
            )
