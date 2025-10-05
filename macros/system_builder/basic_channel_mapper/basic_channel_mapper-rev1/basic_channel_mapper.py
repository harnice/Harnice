import csv
from harnice import fileio, mapped_channels, icd, system_utils

verbose = False

# Load channel map rows from the new system connector list TSV
with open(fileio.path("channel map"), newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f, delimiter="\t")
    channels = list(reader)

# Collect unique merged nets
unique_merged_nets = sorted(
    set(r["merged_net"] for r in channels if r.get("merged_net"))
)

# Look through one merged net at a time
for merged_net in unique_merged_nets:
    if verbose:
        print(f"Mapping channels for merged net: {merged_net}")

    # Look at all channels connected within this net, sorted alphabetically
    net_channels = sorted(
        [r for r in channels if r.get("merged_net") == merged_net],
        key=lambda r: (
            r.get("from_device_refdes", ""),
            r.get("to_device_refdes", ""),
            r.get("from_device_channel_id", ""),
            r.get("to_device_channel_id", ""),
        ),
    )

    for from_channel in net_channels:
        from_key = (
            from_channel.get("from_device_refdes"),
            from_channel.get("from_device_channel_id"),
        )

        if verbose:
            print(f"     From key: {from_key}")

        # Don't map a channel if the "from" has already been mapped
        if mapped_channels.check(from_key):
            if verbose:
                print("          From key already mapped")
            continue

        # Parse channel types
        from_type = icd.parse_channel_type_id(from_channel.get("from_channel_type_id"))
        compatibles_from = icd.compatible_channel_types(
            from_channel.get("from_channel_type_id")
        )

        for to_channel_candidate in net_channels:
            to_key = (
                to_channel_candidate.get("from_device_refdes"),
                to_channel_candidate.get("from_device_channel_id"),
            )

            if verbose:
                print(f"          To key candidate: {to_key}")

            # Don't map a channel to itself
            if to_channel_candidate == from_channel:
                if verbose:
                    print("               To key candidate is the same as from key")
                continue

            # Parse "to" type and its compatibles
            to_type = icd.parse_channel_type_id(
                to_channel_candidate.get("from_channel_type_id")
            )
            compatibles_to = icd.compatible_channel_types(
                to_channel_candidate.get("from_channel_type_id")
            )

            # Backwards-compatible check: either side may declare compatibility
            if not (to_type in compatibles_from or from_type in compatibles_to):
                if verbose:
                    print("               To key candidate is not compatible")
                continue

            # Don't map a channel if it's already been mapped
            if mapped_channels.check(to_key):
                if verbose:
                    print("               To key candidate already mapped")
                continue
            if mapped_channels.check(from_key):
                if verbose:
                    print("               From key candidate already mapped")
                continue

            if verbose:
                print("                    ********* MAPPED *********")
            system_utils.map_and_record(from_key, to_key)
            break  # Stop after first compatible partner
