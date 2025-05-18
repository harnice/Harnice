import os
import json
from harnice import(
    fileio
)

def create_flagnote_matrix_for_all_instances(instances_list_data):
    flagnotes_json = {}
    flagnotes_limit = 15

    for instance in instances_list_data:
        instance_name = instance.get("instance_name")
        item_type = instance.get("item_type")
        flagnotes_json[instance_name] = {"flagnotes": []}

        # open up the instance attributes json file only if it's expected / needed
        flagnote_locations = []
        if item_type not in {"Cable", "Node", "Segment"}:
            attr_path = os.path.join(
                fileio.dirpath("editable_component_data"),
                instance_name,
                f"{instance_name}-attributes.json"
            )
            with open(attr_path, 'r', encoding='utf-8') as f:
                instance_data = json.load(f)
                flagnote_locations = instance_data.get("flagnote_locations", [])

        for flagnote_number in range(flagnotes_limit):
            if item_type == "Cable":
                location = [0, 0]
                supplier = "public"
                design = ""
                text = ""

            elif item_type == "Node":
                location = [0, 0]
                supplier = "public"
                design = ""
                text = ""

            elif item_type == "Segment":
                location = [0, 0]
                supplier = "public"
                design = ""
                text = ""

            else:
                if flagnote_number < len(flagnote_locations):
                    loc = flagnote_locations[flagnote_number]
                    location = [loc.get("angle"), loc.get("distance")]
                else:
                    location = [None, None]
                supplier = "public"
                design = ""
                text = ""

            flagnote = {
                "note_type": "",
                "location": location,
                "supplier": supplier,
                "design": design,
                "text": text
            }

            flagnotes_json[instance_name]["flagnotes"].append(flagnote)

    with open(fileio.path("flagnotes json"), 'w', encoding='utf-8') as f:
        json.dump(flagnotes_json, f, indent=2)

def add_flagnote_content(flagnote_matrix_data, instances_list_data, rev_history_data, buildnotes_data):
    for instance in instances_list_data:
        instance_name = instance.get("instance_name")
        if not instance_name:
            continue  # skip instances without a valid name

        flagnotes = flagnote_matrix_data.get(instance_name, {}).get("flagnotes", [])
        flagnote_number = 0

        # Add instance name as flagnote with "Rectangle" design
        if instance_name.strip():
            if flagnote_number < len(flagnotes):
                flagnotes[flagnote_number]["note_type"] = "instance_name"
                flagnotes[flagnote_number]["design"] = "Rectangle"
                flagnotes[flagnote_number]["text"] = instance_name
                flagnote_number += 1

        # Add BOM item number as flagnote with "Circle" design
        bom_line_number = instance.get("bom_line_number", "").strip()
        if bom_line_number:
            if flagnote_number < len(flagnotes):
                flagnotes[flagnote_number]["note_type"] = "bom_line_number"
                flagnotes[flagnote_number]["design"] = "Circle"
                flagnotes[flagnote_number]["text"] = bom_line_number
                flagnote_number += 1

    # === Save updated flagnote matrix ===
    output_path = fileio.path("flagnotes json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(flagnote_matrix_data, f, indent=2)

def read_flagnote_matrix_file():
    with open(fileio.path("flagnotes json"), 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data