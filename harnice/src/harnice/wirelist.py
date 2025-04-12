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
    with open(fileio.path("instances list"), newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f, delimiter='\t')
        cable_instances = {
            row["instance_name"].strip(): row["length"]
            for row in reader
            if row.get("item_type", "").strip().lower() == "cable"
        }

    # Read wirelist
    with open(fileio.path("wirelist no formats"), newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f, delimiter='\t')
        wirelist_rows = list(reader)
        fieldnames = reader.fieldnames or []

    if "length" not in fieldnames:
        fieldnames.append("length")

    for row in wirelist_rows:
        wire_name = row.get("Wire", "").strip()
        if wire_name in cable_instances:
            row["length"] = cable_instances[wire_name]

    # Write updated wirelist
    with open(fileio.path("wirelist no formats"), 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter='\t')
        writer.writeheader()
        writer.writerows(wirelist_rows)

    return fileio.path("wirelist no formats")

