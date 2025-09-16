
"""
Example usage:
featuretree_utils.runprebuilder("multi_ch_junction_mapper_prebuilder", "https://github.com/kenyonshutt/harnice-library-public", multi_ch_junction_name = "shield", multi_ch_junction_type_ids = [5])
"""


from harnice import system, mapped_channels

# Track mapped channels as (device_refdes, channel_id) tuples
rows = list(system.read_channel_map())
unique_merged_nets = sorted(set(r["merged_net"] for r in rows if r["merged_net"]))

#---------------------------------
# Defaults for globals
DEFAULTS = {
    #name of the channel where multi_ch_junctions are connected
    "multi_ch_junction_name": "shield",

    # list of channel type ids that are considered multi_ch_junctions
    # any channel that has this channel type id will be connected to the added multi_ch_junction_net_name
    "multi_ch_junction_type_ids": [5],

    # list of tuples of [[device_refdes, channel_id], ...]
    # any channel in this list will be connected to the added multi_ch_junction_net_name
    "from_keys": []
}

# Inject defaults if they aren’t already set
for k, v in DEFAULTS.items():
    if k not in globals():
        globals()[k] = v
#---------------------------------

def map_and_record(from_key, multi_ch_junction_key):
    """Helper: map the two channels and mark them as mapped."""
    system.map_channel(from_key, [None,None], multi_ch_junction_key=multi_ch_junction_key)
    mapped_channels.append(from_key)
#---------------------------------

for from_channel in rows:
    multi_ch_junction_key = f"{from_channel["merged_net"]}-{multi_ch_junction_name}"

    from_key = (from_channel["from_device_refdes"], from_channel["from_device_channel_id"])
    
    # don't map a channel if the from has already been mapped
    if mapped_channels.check(from_key):
        continue

    # don't map a channel if it's not part of the specified set
    if from_key in from_keys:
        map_and_record(from_key, multi_ch_junction_key)
        continue

    # don't map if the channel if it doesn't have the multi_ch_junction_channel_type_id we're looking for
    if str(from_channel["channel_type_id"]) not in [str(x) for x in multi_ch_junction_type_ids]:
        continue

    map_and_record(from_key, multi_ch_junction_key)