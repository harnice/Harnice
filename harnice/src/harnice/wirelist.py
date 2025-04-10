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

    with open(fileio.path("wirelist no formats"), 'w', newline='') as file:
        writer = csv.writer(file, delimiter='\t')
        writer.writerow(["Wire", "Subwire", "Source", "SourcePin", "Destination", "DestinationPin"])
        writer.writerows(wirelist)

def add_lengths():
    # Read instances list
    with open(fileio.path("instances list"), newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        # Filter to only rows where item type is Cable
        cable_instances = {
            row["instance name"]: row["length"]
            for row in reader
            if row.get("item type") == "Cable"
        }

    # Read the wirelist
    with open(fileio.path("wirelist no formats"), newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        wirelist_rows = list(reader)
        fieldnames = reader.fieldnames or []

    # Ensure 'length' column exists
    if "length" not in fieldnames:
        fieldnames.append("length")

    # Update wirelist rows with length values
    for row in wirelist_rows:
        instance_name = row.get("wire")
        if instance_name in cable_instances:
            row["length"] = cable_instances[instance_name]

    # Write the updated wirelist back
    with open(fileio.path("wirelist no formats"), 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter='\t')
        writer.writeheader()
        writer.writerows(wirelist_rows)

    # Return the updated path
    return fileio.path("wirelist no formats")


