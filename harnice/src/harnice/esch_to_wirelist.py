import yaml
import csv
import os
from os.path import basename
from inspect import currentframe
from utility import *

# Function to read the YAML file
def read_yaml(file_path):
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)

# Function to generate the wirelist
def generate_wirelist(connections):
    wirelist = []
    for group in connections:
        # Flatten the dictionary structure in the group
        components = {list(item.keys())[0]: list(item.values())[0] for item in group}
        wire = None
        targets = []

        # Identify wire and target components
        for component, pins in components.items():
            if component.startswith("W"):  # Identify wire
                wire = (component, pins)
            elif component.startswith("X"):  # Identify target
                targets.append((component, pins))
        
        # Create connections between targets via the wire
        if wire and len(targets) == 2:
            wire_name, wire_pins = wire
            src_component, src_pins = targets[0]
            dst_component, dst_pins = targets[1]
            
            # Match pins between source and destination through the wire
            for i in range(len(wire_pins)):
                wire_pin = wire_pins[i]
                src_pin = src_pins[i] if isinstance(src_pins, list) else src_pins
                dst_pin = dst_pins[i] if isinstance(dst_pins, list) else dst_pins
                
                # Append as detailed row: wire, subwire, source, sourcepin, destination, destinationpin
                wirelist.append([
                    wire_name, wire_pin, 
                    src_component, src_pin, 
                    dst_component, dst_pin
                ])
    return wirelist

# Function to write the wirelist to a TSV file
def write_tsv(file_path, wirelist):
    with open(file_path, 'w', newline='') as file:
        writer = csv.writer(file, delimiter='\t')
        writer.writerow(["Wire", "Subwire", "Source", "SourcePin", "Destination", "DestinationPin"])
        writer.writerows(wirelist)

def esch_to_wirelist():
    # Read the YAML file
    try:
        data = read_yaml(filepath("harness yaml"))
    except FileNotFoundError:
        print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Error: {filename("harness yaml")} not found in the current directory.")
        exit(1)
    
    # Generate the wirelist
    connections = data.get("connections", [])
    wirelist = generate_wirelist(connections)
    
    # Write the wirelist to a TSV file
    write_tsv(filepath("wirelist nolengths"), wirelist)
    print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Wirelist has been written to {filename("wirelist nolengths")}")

def wirelist_add_lengths():
    return
    #to-do: complete this function