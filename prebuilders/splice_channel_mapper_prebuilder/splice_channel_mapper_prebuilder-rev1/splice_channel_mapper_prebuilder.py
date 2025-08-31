from harnice import system

# Track mapped channels as (box_refdes, channel_id) tuples
mapped_channels = set()
rows = list(system.read_channel_map())
unique_merged_nets = sorted(set(r["merged_net"] for r in rows if r["merged_net"]))

"""
Example usage:
featuretree.runprebuilder("shield_channel_mapper_prebuilder", "public", shield_channel_name = "shield", shield_channel_type_ids = [5])
"""

#---------------------------------
#name of the channel where shields are connected
#shield_channel_name = "shield"

# list of channel type ids that are considered shields
# any channel that has this channel type id will be connected to the added shield_net_name
#shield_channel_type_ids = [5]

# list of tuples of [[box_refdes, channel_id], ...]
# any channel in this list will be connected to the added shield_net_name
#from_keys = []


def map_and_record(from_key, splice_key):
    """Helper: map the two channels and mark them as mapped."""
    print(f"Mapping {from_key} → {splice_key}")
    system.map_channel(from_key, ["",""], splice_key=splice_key)
    mapped_channels.add(from_key)
#---------------------------------

for from_channel in rows:
    splice_key = f"{from_channel["merged_net"]}-{shield_channel_name}"

    from_key = (from_channel["from_box_refdes"], from_channel["from_box_channel_id"])
    print()
    print(f"!!!!!!!!! From key: {from_key}")

    # don't map a channel if the from has already been mapped
    if from_key in mapped_channels:
        print(f"!!!!!!!!! From key already mapped: part of {mapped_channels}")
        continue

    # don't map a channel if it's not part of the specified set
    if from_key in from_keys:
        print(f"********* mapped {from_key}")
        map_and_record(from_key, splice_key)
        continue

    # don't map if the channel if it doesn't have the shield_channel_type_id we're looking for
    if str(from_channel["channel_type_id"]) not in [str(x) for x in shield_channel_type_ids]:
        print(f"!!!!!!!!! From channel not in shield_channel_type_ids: {from_channel['channel_type_id']} not in {shield_channel_type_ids}")
        continue

    print(f"********* mapped {from_key}")
    map_and_record(from_key, splice_key)