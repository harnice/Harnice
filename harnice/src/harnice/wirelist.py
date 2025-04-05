import yaml
import csv
import os
from os.path import basename
from inspect import currentframe
import fileio
import yaml
import csv
from os.path import basename
from inspect import currentframe

def newlist():
    try:
        with open(fileio.path("harness yaml"), 'r') as file:
            yaml_data = yaml.safe_load(file)
    except FileNotFoundError:
        print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Error: {fileio.name('harness yaml')} not found in the current directory.")
        exit(1)

    # Extract connections and build wirelist
    connections = yaml_data.get("connections", [])
    wirelist = []

    for group in connections:
        components = {list(item.keys())[0]: list(item.values())[0] for item in group}
        wire = None
        targets = []

        for component, pins in components.items():
            if component.startswith("W"):
                wire = (component, pins)
            elif component.startswith("X"):
                targets.append((component, pins))

        if wire and len(targets) == 2:
            wire_name, wire_pins = wire
            src_component, src_pins = targets[0]
            dst_component, dst_pins = targets[1]

            for i in range(len(wire_pins)):
                wire_pin = wire_pins[i]
                src_pin = src_pins[i] if isinstance(src_pins, list) else src_pins
                dst_pin = dst_pins[i] if isinstance(dst_pins, list) else dst_pins

                wirelist.append([
                    wire_name, wire_pin,
                    src_component, src_pin,
                    dst_component, dst_pin
                ])

    with open(fileio.path("wirelist nolengths"), 'w', newline='') as file:
        writer = csv.writer(file, delimiter='\t')
        writer.writerow(["Wire", "Subwire", "Source", "SourcePin", "Destination", "DestinationPin"])
        writer.writerows(wirelist)

    print(f"Wirelist has been written to {fileio.name('wirelist nolengths')}")

def add_lengths():
    # Load the TSV files
    instances_df = pd.read_csv(filepath("instances list"), sep='\t')
    wirelist_df = pd.read_csv(filepath("wirelist lengths"), sep='\t')

    # Filter instances to only include rows where "item type" is "Cable"
    instances_df = instances_df[instances_df["item type"] == "Cable"]

    # Make sure the 'length' column exists in the wirelist, or create it
    if 'length' not in wirelist_df.columns:
        wirelist_df['length'] = None

    # Loop through each row in instances_df
    for _, instance_row in instances_df.iterrows():
        instance_name = instance_row.get("instance name")
        length_value = instance_row.get("length")

        # Apply the length to matching wirelist rows
        matching_rows = wirelist_df["wire"] == instance_name
        wirelist_df.loc[matching_rows, "length"] = length_value

    # Save the updated wirelist
    wirelist_df.to_csv(filepath("wirelist lengths"), sep='\t', index=False)

    # Return the path
    return filepath("wirelist lengths")