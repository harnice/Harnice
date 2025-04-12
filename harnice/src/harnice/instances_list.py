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

def add_cable_lengths():
    # Load JSON graph data
    with open(fileio.path("connections to graph"), "r") as json_file:
        graph_data = json.load(json_file)

    tsv_path = fileio.path("instances list")

    # Read the TSV into memory
    with open(tsv_path, newline='') as tsv_file:
        reader = csv.DictReader(tsv_file, delimiter='\t')
        rows = list(reader)
        fieldnames = reader.fieldnames or []

    # Ensure the 'length' column is present
    if "length" not in fieldnames:
        fieldnames.append("length")

    # Modify rows in memory
    for row in rows:
        if row.get("item_type") == "Cable":
            instance = row.get("instance_name")
            if instance in graph_data:
                row["length"] = graph_data[instance].get("wirelength", "")
            else:
                row["length"] = ""
        else:
            # Preserve existing value or blank
            row["length"] = row.get("length", "")

    # Write all rows back to the same TSV
    with open(tsv_path, "w", newline='') as tsv_file:
        writer = csv.DictWriter(tsv_file, fieldnames=fieldnames, delimiter='\t')
        writer.writeheader()
        writer.writerows(rows)

from collections import defaultdict
def convert_to_bom():
    # Track MPN groups
    mpn_groups = defaultdict(lambda: {"qty": 0, "item_type": "", "supplier": ""})

    # Read the instances list
    with open(fileio.path("instances list"), newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            mpn = row.get("mpn", "").strip()
            if not mpn:
                continue  # Skip rows without MPN

            mpn_data = mpn_groups[mpn]
            mpn_data["qty"] += 1
            mpn_data["item_type"] = row.get("item_type", "")
            mpn_data["supplier"] = row.get("supplier", "")

    # Prepare output
    bom_rows = []
    for i, (mpn, data) in enumerate(mpn_groups.items(), start=1):
        bom_rows.append({
            "bom_line_number": i,
            "qty": data["qty"],
            "mpn": mpn,
            "item_type": data["item_type"],
            "supplier": data["supplier"],
        })

    # Define column order
    fieldnames = ["bom_line_number", "mpn", "item_type", "qty", "supplier"]

    # Write to harness bom TSV
    with open(fileio.path("harness bom"), 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter='\t')
        writer.writeheader()
        writer.writerows(bom_rows)

    return fileio.path("harness bom")
    