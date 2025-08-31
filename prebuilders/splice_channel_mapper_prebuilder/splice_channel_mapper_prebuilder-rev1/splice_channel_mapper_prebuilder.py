
"""
Example usage:
featuretree.runprebuilder("splice_channel_mapper_prebuilder", "public", splice_channel_name = "shield", splice_channel_type_ids = [5])
"""


from harnice import system, mapped_channels

# Track mapped channels as (box_refdes, channel_id) tuples
rows = list(system.read_channel_map())
unique_merged_nets = sorted(set(r["merged_net"] for r in rows if r["merged_net"]))

#---------------------------------
# Defaults for globals
DEFAULTS = {
    #name of the channel where splices are connected
    "splice_channel_name": "shield",

    # list of channel type ids that are considered splices
    # any channel that has this channel type id will be connected to the added splice_net_name
    "splice_channel_type_ids": [5],

    # list of tuples of [[box_refdes, channel_id], ...]
    # any channel in this list will be connected to the added splice_net_name
    "from_keys": []
}

# Inject defaults if they aren’t already set
for k, v in DEFAULTS.items():
    if k not in globals():
        globals()[k] = v
#---------------------------------

def map_and_record(from_key, splice_key):
    """Helper: map the two channels and mark them as mapped."""
    print(f"Mapping {from_key} → {splice_key}")
    system.map_channel(from_key, ["",""], splice_key=splice_key)
    mapped_channels.append(from_key)
#---------------------------------

for from_channel in rows:
    splice_key = f"{from_channel["merged_net"]}-{splice_channel_name}"

    from_key = (from_channel["from_box_refdes"], from_channel["from_box_channel_id"])
    print()

    # don't map a channel if the from has already been mapped
    if mapped_channels.check(from_key):
        continue

    # don't map a channel if it's not part of the specified set
    if from_key in from_keys:
        map_and_record(from_key, splice_key)
        continue

    # don't map if the channel if it doesn't have the splice_channel_type_id we're looking for
    if str(from_channel["channel_type_id"]) not in [str(x) for x in splice_channel_type_ids]:
        continue

    map_and_record(from_key, splice_key)