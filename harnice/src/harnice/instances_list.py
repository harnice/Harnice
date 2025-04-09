import yaml
import json
import csv
import fileio

def make_new_list():
    with open(fileio.path("instances list"), "w", newline="") as tsvfile:
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

def add_connectors():
    with open(fileio.path("harness yaml"), "r") as file:
        yaml_data_parsed = yaml.safe_load(file)

    connectors = yaml_data_parsed.get("connectors", {})

    for instance_name, connector in connectors.items():
        mpn = connector.get("mpn", "")
        supplier = connector.get("supplier", "")
        component_instances = []

        with open(fileio.path("instances list"), "a", newline="") as tsvfile:
            writer = csv.writer(tsvfile, delimiter="\t")

            for component in connector.get("additional_components", []):
                component_mpn = component.get("mpn", "")
                component_type = component.get("type", "")
                component_supplier = component.get("supplier", "")

                suffix = "bs" if component_type.lower() == "backshell" else component_type.lower()
                component_instance_name = f"{instance_name}.{suffix}"
                component_instances.append(component_instance_name)

                # Write row for the additional component
                writer.writerow([
                    component_instance_name,
                    "",
                    component_mpn,
                    component_type,
                    "",
                    instance_name,
                    component_supplier,
                    "", "", "", ""
                ])

        # Write connector row
        with open(fileio.path("instances list"), "a", newline="") as tsvfile:
            writer = csv.writer(tsvfile, delimiter="\t")
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

def add_cables():
    with open(fileio.path("harness yaml"), "r") as file:
        yaml_data_parsed = yaml.safe_load(file)

    cables = yaml_data_parsed.get("cables", {})

    with open(fileio.path("instances list"), "a", newline="") as tsvfile:
        writer = csv.writer(tsvfile, delimiter="\t")

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

def add_formboard_segments():
    with open(fileio.path("formboard graph definition"), "r") as f:
        formboard_data = yaml.safe_load(f)

    with open(fileio.path("instances list"), "a", newline="") as tsvfile:
        writer = csv.writer(tsvfile, delimiter="\t")

        for segment_name, segment in formboard_data.items():
            writer.writerow([
                segment_name,
                "",
                "",
                "Segment",
                "",
                "",
                "",
                segment.get("length", ""),
                segment.get("diameter", ""),
                "", ""
            ])
