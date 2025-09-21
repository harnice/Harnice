from harnice import system_utils, mapped_channels

# Track mapped channels as (device_refdes, channel_id) tuples
rows = list(system_utils.read_channel_map())
unique_merged_nets = sorted(set(r["merged_net"] for r in rows if r["merged_net"]))


def map_and_record(from_key, to_key):
    """Helper: map the two channels and mark them as mapped."""
    system_utils.map_channel(from_key, to_key)
    mapped_channels.append(from_key)
    mapped_channels.append(to_key)


# look through one merged net at a time
for merged_net in unique_merged_nets:

    # look at all channels connected within this net
    net_channels = [r for r in rows if r["merged_net"] == merged_net]

    for from_channel in net_channels:
        from_key = (
            from_channel["from_device_refdes"],
            from_channel["from_device_channel_id"],
        )

        # don't map a channel if the from has already been mapped
        if mapped_channels.check(from_key):
            continue

        compatible_channel_type_ids = system_utils.compatible_channel_type_ids(from_key)

        for to_channel_candidate in net_channels:
            # don't map a channel to itself
            if to_channel_candidate == from_channel:
                continue

            # don't map if the channel type is not compatible
            if (
                str(to_channel_candidate["channel_type_id"])
                not in compatible_channel_type_ids
            ):
                continue

            # don't map a channel if it's already been mapped
            to_key = (
                to_channel_candidate["from_device_refdes"],
                to_channel_candidate["from_device_channel_id"],
            )
            if mapped_channels.check(to_key):
                continue

            map_and_record(from_key, to_key)
            break  # stop after first compatible partner
