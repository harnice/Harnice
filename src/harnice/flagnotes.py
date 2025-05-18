
import os
import json
import fileio

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
                "location": location,
                "supplier": supplier,
                "design": design,
                "text": text
            }

            flagnotes_json[instance_name]["flagnotes"].append(flagnote)

    with open(fileio.path("flagnotes json"), 'w', encoding='utf-8') as f:
        json.dump(flagnotes_json, f, indent=2)

