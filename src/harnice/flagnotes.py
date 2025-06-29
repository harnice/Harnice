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
            # Only assign bubble_text if it's blank
            bubble_counters[key] = bubble_counters.get(key, 0) + 1
            row["bubble_text"] = str(bubble_counters[key])
        else:
            # Preserve existing bubble_text
            row["bubble_text"] = bubble_text

    # === Step 6: Write to flagnotes list ===
    with open(fileio.path('flagnotes list'), 'a', newline='', encoding='utf-8') as f_list:
        writer_list = csv.DictWriter(f_list, fieldnames=FLAGNOTES_COLUMNS, delimiter='\t')
        writer_list.writerows(expanded_rows)

def make_note_drawings():
    pass