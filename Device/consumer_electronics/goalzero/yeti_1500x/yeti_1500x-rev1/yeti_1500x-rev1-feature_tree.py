
from harnice.lists import signals_list
from harnice.products import chtype

signals_list.new()

# signal_name (from channel_types list) : cavity or other identifier on connector
barrel_pinout = {
    "pos": "pin",
    "neg": "ring"
}

powerpole_pinout = {
    "pos": "red",
    "neg": "black"
}

usb_c_pinout = {
    "all": "all"
}

usb_a_pinout = {
    "pos": 1,
    "neg": 4
}

american_outlet = {
    "live":"live",
    "neutral":"neutral",
    "earth":"earth"
}

for row in [
    ["12vdc_barrel_out-1", "GOALZERO_6MM_BARREL", (13, "https://github.com/harnice/harnice-library-public"), barrel_pinout],
    ["12vdc_barrel_out-2", "GOALZERO_6MM_BARREL", (13, "https://github.com/harnice/harnice-library-public"), barrel_pinout],
    ["charge_in-barrel", "GOALZERO_8MM_BARREL", (20, "https://github.com/harnice/harnice-library-public"), barrel_pinout],
    ["car_port", "CIG_LIGHTER", (21, "https://github.com/harnice/harnice-library-public"), barrel_pinout],
    ["charge_in-powerpole", "PP15-2", (10, "https://github.com/harnice/harnice-library-public"), powerpole_pinout],
    ["12vdc_powerpole_out", "PP15-2", (19, "https://github.com/harnice/harnice-library-public"), powerpole_pinout],
    ["usbc-pd", "USBC_RECEPT", (15, "https://github.com/harnice/harnice-library-public"), usb_c_pinout],
    ["usbc-normal", "USBC_RECEPT", (16, "https://github.com/harnice/harnice-library-public"), usb_c_pinout],
    ["usba-1", "USBA_RECEPT", (22, "https://github.com/harnice/harnice-library-public"), usb_a_pinout],
    ["usba-2", "USBA_RECEPT", (22, "https://github.com/harnice/harnice-library-public"), usb_a_pinout],
    ["AC_out-1", "NEMA_5-15R", (17, "https://github.com/harnice/harnice-library-public"), american_outlet],
    ["AC_out-2", "NEMA_5-15R", (17, "https://github.com/harnice/harnice-library-public"), american_outlet],
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
