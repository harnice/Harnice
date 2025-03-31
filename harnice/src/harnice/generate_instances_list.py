import yaml
import csv
from pathlib import Path
from utility import *  # Assumes filepath() is defined here

def generate_instances_list():
    # Get the full TSV path
    tsv_full_path = Path(filepath("instances list"))
    tsv_full_path.parent.mkdir(parents=True, exist_ok=True)

    # Load YAML data
    with open(Path(filepath("wireviz yaml")), "r") as file:
        parsed = yaml.safe_load(file)

    connectors = parsed.get("connectors", {})
    cables = parsed.get("cables", {})

    with open(tsv_full_path, "w", newline="") as tsvfile:
        writer = csv.writer(tsvfile, delimiter="\t")

        # Write header
        writer.writerow([
            "instance_name",
            "bom_line",
            "mpn",
            "item_type",
            "child_instance",
            "parent_instance",
            "supplier",
            "length",
            "diameter",
            "translate_formboard",
            "translate_bs"
        ])

        # Connectors
        for instance_name, connector in connectors.items():
            mpn = connector.get("mpn", "")
            supplier = connector.get("supplier", "")

            # Connector row
            writer.writerow([
                instance_name,  # instance_name
                "",             # bom_line
                mpn,            # mpn
                "Connector",    # item_type
                mpn,            # child_instance
                "",             # parent_instance
                supplier,       # supplier
                "", "", "", ""  # length, diameter, translate_formboard, translate_bs
            ])

            # Additional components
            for component in connector.get("additional_components", []):
                component_mpn = component.get("mpn", "")
                component_type = component.get("type", "")
                component_supplier = component.get("supplier", "")

                writer.writerow([
                    instance_name,           # instance_name
                    "",                      # bom_line
                    component_mpn,           # mpn
                    component_type,          # item_type
                    component_mpn,           # child_instance
                    instance_name,           # parent_instance
                    component_supplier,      # supplier
                    "", "", "", ""           # length, diameter, translate_formboard, translate_bs
                ])

        # Cables
        for cable_name, cable in cables.items():
            writer.writerow([
                cable_name,   # instance_name
                "",           # bom_line
                "",           # mpn
                "Cable",      # item_type
                "",           # child_instance
                "",           # parent_instance
                "",           # supplier
                "", "", "", ""  # length, diameter, translate_formboard, translate_bs
            ])
