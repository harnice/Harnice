import yaml
import csv
from pathlib import Path
from utility import *  # Assumes filepath() is defined here

def generate_instances_list():
    tsv_full_path = Path(filepath("instances list"))
    tsv_full_path.parent.mkdir(parents=True, exist_ok=True)

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

        # Process connectors
        for instance_name, connector in connectors.items():
            mpn = connector.get("mpn", "")
            supplier = connector.get("supplier", "")
            component_instances = []

            for component in connector.get("additional_components", []):
                component_mpn = component.get("mpn", "")
                component_type = component.get("type", "")
                component_supplier = component.get("supplier", "")

                # Use .bs suffix for Backshell, otherwise use .{type.lower()}
                if component_type.lower() == "backshell":
                    suffix = "bs"
                else:
                    suffix = component_type.lower()

                component_instance_name = f"{instance_name}.{suffix}"
                component_instances.append(component_instance_name)

                # Write row for the component
                writer.writerow([
                    component_instance_name,       # instance_name like X1.bs
                    "",                            # bom_line
                    component_mpn,                 # mpn
                    component_type,                # item_type
                    component_mpn,                 # child_instance
                    instance_name,                 # parent_instance
                    component_supplier,            # supplier
                    "", "", "", ""                 # length, diameter, translate_formboard, translate_bs
                ])

            # Write connector row
            writer.writerow([
                instance_name,
                "",
                mpn,
                "Connector",
                ", ".join(component_instances) if component_instances else "",
                "",
                supplier,
                "", "", "", ""
            ])

        # Process cables
        for cable_name, cable in cables.items():
            writer.writerow([
                cable_name,
                "",
                "",
                "Cable",
                "",
                "",
                "",
                "", "", "", ""
            ])
