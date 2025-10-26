"""
Example usage:
featuretree_utils.run_macro("multi_channel_junction_mapper", "https://github.com/kenyonshutt/harnice-library-public", lib_subpath="build_macros", multi_ch_junction_name = "shield", multi_ch_junction_type_ids = [5])

args:
- multi_ch_junction_name: name of the channel where multi_ch_junctions are connected
- multi_ch_junction_type_ids: list of channel type ids that are considered multi_ch_junctions
- from_keys: list of tuples of [[device_refdes, channel_id], ...]
"""

from harnice import system
from harnice.lists import mapped_channels
from harnice.utils import system_utils

def file_structure():
    return {}

def generate_structure():
    pass

# Track mapped channels as (device_refdes, channel_id) tuples
rows = list(system.read_channel_map())
unique_merged_nets = sorted(set(r["merged_net"] for r in rows if r["merged_net"]))

# ---------------------------------
# Defaults for globals
DEFAULTS = {
    # name of the channel where multi_ch_junctions are connected
    "multi_ch_junction_name": "shield",
    # list of channel type ids that are considered multi_ch_junctions
    # any channel that has this channel type id will be connected to the added multi_ch_junction_net_name
    "multi_ch_junction_type_ids": [5],
    # list of tuples of [[device_refdes, channel_id], ...]
    # any channel in this list will be connected to the added multi_ch_junction_net_name
    "from_keys": [],
}

# Inject defaults if they aren’t already set
for k, v in DEFAULTS.items():
    if k not in globals():
        globals()[k] = v


for from_channel in rows:
    multi_ch_junction_key = f"{from_channel['merged_net']}-{multi_ch_junction_name}"

    from_key = (
        from_channel["from_device_refdes"],
        from_channel["from_device_channel_id"],
    )

    # don't map a channel if the from has already been mapped
    if mapped_channels.check(from_key):
        continue

    # don't map a channel if it's not part of the specified set
    if from_key in from_keys:
        system_utils.map_and_record(from_key, multi_ch_junction_key)
        continue

    # don't map if the channel if it doesn't have the multi_ch_junction_channel_type we're looking for
    if str(from_channel["channel_type"]) not in [
        str(x) for x in multi_ch_junction_type_ids
    ]:
        continue

    system_utils.map_and_record(from_key, multi_ch_junction_key)
