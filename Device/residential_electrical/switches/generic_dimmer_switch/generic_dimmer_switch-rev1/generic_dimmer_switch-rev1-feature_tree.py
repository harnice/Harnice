
from harnice.lists import signals_list
from harnice.products import chtype

american_outlet = {
    "live":"live",
    "neutral":"neutral",
    "earth":"earth"
}

signals_list.new()

for row in [
    ["in", "wire_nuts", (18, "https://github.com/harnice/harnice-library-public"), american_outlet],
    ["out", "wire_nuts", (24, "https://github.com/harnice/harnice-library-public"), american_outlet],
]:

    channel_name = row[0]
    connector_mpn = row[1]
    channel_type = row[2]
    pinout = row[3]

    for signal in chtype.signals(channel_type):
        signals_list.append(
            channel_id=channel_name,
            signal=signal,
            connector_name=channel_name,
            cavity=pinout.get(signal),
            channel_type=channel_type,
            connector_mpn=connector_mpn
        )
