from harnice import system

# Take a static snapshot of the channel map
rows = list(system.read_channel_map())
mapped_nets = []

for net in rows:
    current_net = net["merged_net"]

    # Only process each net once
    if current_net not in mapped_nets:
        mapped_nets.append(current_net)
        continue

    # Gather all rows for this net
    from_rows = [r for r in rows if r["merged_net"] == current_net]
    mapped_to_channels = set()

    for from_row in from_rows:
        for to_row in from_rows:
            if to_row == from_row:
                continue

            # Skip if we've already mapped this to_row
            if (to_row["from_box_refdes"], to_row["from_box_channel_id"]) in mapped_to_channels:
                continue

            # Check channel type compatibility
            compat_ids = [
                t.strip()
                for t in str(from_row["compatible_channel_type_ids"]).split(",")
                if t.strip()
            ]
            if str(to_row["channel_type_id"]) not in compat_ids:
                continue

            # Call the existing map_channel function
            system.map_channel(
                from_box_refdes=from_row["from_box_refdes"],
                from_box_channel_id=from_row["from_box_channel_id"],
                to_box_refdes=to_row["from_box_refdes"],
                to_box_channel_id=to_row["from_box_channel_id"],
            )

            mapped_to_channels.add(
                (to_row["from_box_refdes"], to_row["from_box_channel_id"])
            )
            break  # stop after first match for this from_row
