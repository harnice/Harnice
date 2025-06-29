import os
import json
import csv
from dotenv import load_dotenv, dotenv_values
from harnice import(
    fileio,
    instances_list,
    component_library
)

# === Global Columns Definition ===
FLAGNOTES_COLUMNS = [
    "note_type",
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

    # === Step 3: Read revision history rows and construct flagnotes ===
    revision_rows = []
    with open(fileio.path('revision history'), newline='', encoding='utf-8') as f_rev:
        reader = csv.DictReader(f_rev, delimiter='\t')
        for rev_row in reader:
            affected = rev_row.get("affectedinstances", "").strip()
            if affected:
                instances = [i.strip() for i in affected.split(',') if i.strip()]
                for instance in instances:
                    revision_rows.append({
                        "note_type": "rev_change_callout",
                        "note": "",
                        "shape": "rev_change_callout",
                        "shape_supplier": "public",
                        "bubble_text": fileio.partnumber("rev"),
                        "affectedinstances": instance
                    })

    # === Step 4: Add auto-generated flagnotes from instance list ===
    auto_generated = []
    instances = instances_list.read_instance_rows()
    for instance in instances:
        item_type = instance.get("item_type", "").strip()
        instance_name = instance.get("instance_name", "").strip()
        if item_type in {"Connector", "Backshell"}:
            auto_generated.append({
                "note_type": "part_name",
                "note": "",
                "shape": "part_name",
                "shape_supplier": "public",
                "bubble_text": instance_name,
                "affectedinstances": instance_name
            })
            auto_generated.append({
                "note_type": "bom_item",
                "note": "",
                "shape": "bom_item",
                "shape_supplier": "public",
                "bubble_text": "",
                "affectedinstances": instance_name
            })

    all_rows = manual_rows + revision_rows + auto_generated

    # === Step 5: Expand rows with multiple affected instances ===
    expanded_rows = []
    for row in all_rows:
        affected = row.get('affectedinstances', '').strip()
        instances = [i.strip() for i in affected.split(',') if i.strip()] or ['']
        for instance in instances:
            new_row = row.copy()
            new_row['affectedinstances'] = instance
            expanded_rows.append(new_row)

    # === Step 6: Sort by note_type priority and affectedinstances ===
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

    # === Step 7: Assign bubble_text where blank (per note_type + affectedinstances) ===
    bubble_counters = {}
    for row in expanded_rows:
        note_type = row.get("note_type", "").strip()
        instance = row.get("affectedinstances", "").strip()
        bubble_text = row.get("bubble_text", "").strip()

        key = (note_type, instance)
        if not bubble_text:
            bubble_counters[key] = bubble_counters.get(key, 0) + 1
            row["bubble_text"] = str(bubble_counters[key])
        else:
            row["bubble_text"] = bubble_text

    # === Step 8: Write all flagnotes to list ===
    with open(fileio.path('flagnotes list'), 'a', newline='', encoding='utf-8') as f_list:
        writer_list = csv.DictWriter(f_list, fieldnames=FLAGNOTES_COLUMNS, delimiter='\t')
        writer_list.writerows(expanded_rows)

def make_note_drawings():
    instances = instances_list.read_instance_rows()
    
    for instance in instances:
        if instance.get("item_type", "").lower() != "flagnote":
            continue

        instance_name = instance.get("instance_name")
        destination_directory=os.path.join(fileio.dirpath("uneditable_instance_data"), instance_name)

        # Ensure the destination directory exists
        os.makedirs(destination_directory, exist_ok=True)

        # Pull the item from the library
        component_library.pull_item_from_library(
            supplier=instance.get("supplier"),
            lib_subpath="flagnotes",
            mpn=instance.get("mpn"),
            destination_directory=destination_directory,
            used_rev=None,
            item_name=instance_name
        )
