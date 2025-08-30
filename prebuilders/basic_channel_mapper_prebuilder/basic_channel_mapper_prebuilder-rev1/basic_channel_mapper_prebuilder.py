from harnice import system

# Track mapped channels as (box_refdes, channel_id) tuples
mapped_channels = set()

rows = list(system.read_channel_map())
unique_nets = sorted(set(r["merged_net"] for r in rows if r["merged_net"]))

for net in unique_nets:
    # all rows belonging to this net
    net_rows = [r for r in rows if r["merged_net"] == net]

    for from_row in net_rows:
        from_key = (from_row["from_box_refdes"], from_row["from_box_channel_id"])
        if from_key in mapped_channels:
            continue  # already mapped

        # find a compatible partner
        compat_ids = [
            t.strip()
            for t in str(from_row["compatible_channel_type_ids"]).split(",")
            if t.strip()
        ]

        for to_row in net_rows:
            if to_row == from_row:
                continue

            to_key = (to_row["from_box_refdes"], to_row["from_box_channel_id"])
            if to_key in mapped_channels:
                continue  # already mapped

            if str(to_row["channel_type_id"]) not in compat_ids:
                continue  # incompatible

            # Perform mapping
            print(f"Mapping {from_key} → {to_key}")
            system.map_channel(
                from_box_refdes=from_row["from_box_refdes"],
                from_box_channel_id=from_row["from_box_channel_id"],
                to_box_refdes=to_row["from_box_refdes"],
                to_box_channel_id=to_row["from_box_channel_id"],
            )

            # Mark both as mapped
            mapped_channels.add(from_key)
            mapped_channels.add(to_key)
            break  # stop after first partner
