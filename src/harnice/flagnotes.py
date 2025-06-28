import os
import json
import csv
from harnice import(
    fileio
)

# === Global Columns Definition ===
FLAGNOTES_COLUMNS = [
    "notetype",
    "note",
    "shape",
    "shape_supplier",
    "bubble_text",
    "affectedinstances"
]

def ensure_manual_list_exists():
    if not os.path.exists(fileio.path('flagnotes manual')):
        with open(fileio.path('flagnotes manual'), 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=FLAGNOTES_COLUMNS, delimiter='\t')
            writer.writeheader()

def compile_all_flagnotes():
    # === Step 1: Reset only "flagnotes list" TSV ===
    with open(fileio.path('flagnotes list'), 'w', newline='', encoding='utf-8') as f_list:
        writer_list = csv.DictWriter(f_list, fieldnames=FLAGNOTES_COLUMNS, delimiter='\t')
        writer_list.writeheader()

    # === Step 2: Read all manual rows ===
    manual_rows = []
    if os.path.exists(fileio.path('flagnotes manual')):
        with open(fileio.path('flagnotes manual'), newline='', encoding='utf-8') as f_manual:
            reader = csv.DictReader(f_manual, delimiter='\t')
            manual_rows = list(reader)

    # === Step 3: Expand rows with multiple affected instances ===
    expanded_rows = []
    for row in manual_rows:
        affected = row.get('affectedinstances', '').strip()
        instances = [i.strip() for i in affected.split(',') if i.strip()] or ['']
        for instance in instances:
            new_row = row.copy()
            new_row['affectedinstances'] = instance
            expanded_rows.append(new_row)

    # === Step 4: Sort by note_type priority and affectedinstances ===
    note_priority = {
        "part_name": 0,
        "bom_item": 1,
        "rev_change_callout": 2,
        "engineering_note": 3,
        "buildnote": 4,
        "backshell_clock": 5
    }

    expanded_rows.sort(key=lambda row: (
        note_priority.get(row.get("note_type", "").strip(), 99),
        row.get("affectedinstances", "").strip()
    ))

    # === Step 5: Assign bubble_text numbers where blank (per note_type + affectedinstances pair) ===
    bubble_counters = {}  # key: (note_type, instance)
    for row in expanded_rows:
        note_type = row.get("note_type", "").strip()
        instance = row.get("affectedinstances", "").strip()
        bubble_text = row.get("bubble_text", "").strip()

        key = (note_type, instance)
        if not bubble_text:
            bubble_counters[key] = bubble_counters.get(key, 0) + 1
            row["bubble_text"] = str(bubble_counters[key])

    # === Step 6: Write to flagnotes list ===
    with open(fileio.path('flagnotes list'), 'a', newline='', encoding='utf-8') as f_list:
        writer_list = csv.DictWriter(f_list, fieldnames=FLAGNOTES_COLUMNS, delimiter='\t')
        writer_list.writerows(expanded_rows)

def add_notes_to_instances_list(instances_list_data):
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
                "shape_supplier": supplier,
                "shape": design,
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