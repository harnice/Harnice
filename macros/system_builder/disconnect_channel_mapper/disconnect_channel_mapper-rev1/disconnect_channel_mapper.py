import csv
from harnice import fileio, system_utils

verbose = True

print("6")

# Load disconnect channel map rows (always reopens the file)
def disconnect_channel_map():
    with open(fileio.path("disconnect channel map"), newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        return list(reader)

print("12")

for required_channel in disconnect_channel_map():
    print("17")

    # skip available channel rows (A-side empty)
    if required_channel.get("A-side_device_refdes") in [None, ""]:
        continue

    disconnect_refdes = required_channel.get("disconnect_refdes")

    print("22")

    available_candidates = []
    for available_channel in disconnect_channel_map():
        if available_channel.get("A-side_device_refdes") in [None, ""]:
            if available_channel.get("disconnect_refdes") == disconnect_refdes:
                available_candidates.append(available_channel)

    print("30")
    print(f"{required_channel.get('A-side_device_refdes')}.{required_channel.get('A-side_device_channel_id')}")

    if not available_candidates:
        print("No available candidates found")
    else:
        for candidate in available_candidates:
            print(f"!!!!!!!!!!! {candidate.get('disconnect_refdes')}.{candidate.get('disconnect_channel_id')}")
