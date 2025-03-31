import yaml
import csv
from pathlib import Path
from utility import *  # Assuming filepath() is defined here

# Load YAML data
with open(Path(filepath("wireviz yaml")), "r") as file:
    parsed = yaml.safe_load(file)

# Get the connectors section
connectors = parsed.get("connectors", {})

# Write to TSV
with open(Path(filepath("instances list")), "w", newline="") as tsvfile:
    writer = csv.writer(tsvfile, delimiter="\t")
    
    # Write header
    writer.writerow(["Connector Name", "MPN", "Supplier", "Type"])
    
    for name, connector in connectors.items():
        # Main connector
        writer.writerow([
            name,
            connector.get("mpn", ""),
            connector.get("supplier", ""),
            ""
        ])
        
        # Additional components
        for component in connector.get("additional_components", []):
            writer.writerow([
                name,
                component.get("mpn", ""),
                component.get("supplier", ""),
                component.get("type", "")
            ])
