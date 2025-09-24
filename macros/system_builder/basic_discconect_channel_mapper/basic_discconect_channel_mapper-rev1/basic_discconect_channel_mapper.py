import csv
from harnice import fileio, system_utils

with open(fileio.path("channel map"), newline="", encoding="utf-8") as f:
    channel_map = list(csv.DictReader(f, delimiter="\t"))

with open (fileio.path("system connector list"), newline="", encoding="utf-8") as f:
    connector_list = list(csv.DictReader(f, delimiter="\t"))

for channel in channel_map:
    from_ch_key = (
        channel.get("from_device_refdes"),
        channel.get("from_device_channel_id"),
    )
    from_cn_key = (channel.get("from_device_refdes"), system_utils.connector_of_channel(from_ch_key))
    to_ch_key = (
        channel.get("to_device_refdes"),
        channel.get("to_device_channel_id"),
    )
    if to_ch_key == (None, None):
        continue
    to_cn_key = (channel.get("to_device_refdes"), system_utils.connector_of_channel(to_ch_key))

    for cn_key in connector_list:
        if cn_key.get("device_refdes") == from_cn_key[0] and cn_key.get("connector") == from_cn_key[1]:
            from_net = cn_key.get("net")
        if cn_key.get("device_refdes") == to_cn_key[0] and cn_key.get("connector") == to_cn_key[1]:
            to_net = cn_key.get("net")

    if from_net == to_net:
        #no disconnects found
        break

    else:
        