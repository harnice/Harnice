import os
import json
import csv
import re
import math
from dotenv import load_dotenv, dotenv_values
from harnice import(
    fileio,
    instances_list,
    component_library
)

# === Global Columns Definition ===
MANUAL_FLAGNOTES_COLUMNS = [
    "note_type",
    "note_text",
    "shape",
    "shape_supplier",
    "bubble_text",
    "affectedinstances"
]

def ensure_manual_list_exists():
    if not os.path.exists(fileio.path('flagnotes manual')):
        with open(fileio.path('flagnotes manual'), 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=MANUAL_FLAGNOTES_COLUMNS, delimiter='\t')
            writer.writeheader()

def read_manual_list():
    with open(fileio.path('flagnotes manual'), newline='', encoding='utf-8') as f_manual:
        return list(csv.DictReader(f_manual, delimiter='\t'))

def read_revhistory():
    with open(fileio.path("revision history"), newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            yield row

def flagnote_location(affected_instance_name, note_number):
    """
    Returns (translate_x, translate_y) from flagnote_locations in the instance's attributes file.
    Returns empty strings if unavailable.
    """
    path = os.path.join(
        fileio.dirpath("imported_instances"),
        affected_instance_name,
        affected_instance_name + "-attributes.json"
    )

    if not os.path.exists(path):
        return "", ""

    with open(path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            return "", ""

    locations = data.get("flagnote_locations", [])
    if note_number >= len(locations):
        return "", ""

    location = locations[note_number]
    angle = location.get("angle", 0)
    distance = location.get("distance", 0)
    radians = math.radians(angle)
    x = round(math.cos(radians) * distance, 5)
    y = round(math.sin(radians) * distance, 5)
    return x, y

def make_note_drawings():
    instances = instances_list.read_instance_rows()

    for instance in instances:
        if instance.get("item_type", "").lower() != "flagnote":
            continue

        instance_name = instance.get("instance_name")
        parent_instance = instance.get("parent_instance", "").strip()

        destination_directory = os.path.join(fileio.dirpath("generated_instances_do_not_edit"), instance_name)
        os.makedirs(destination_directory, exist_ok=True)

        # === Pull library item ===
        component_library.pull_item_from_library(
            supplier=instance.get("supplier"),
            lib_subpath="flagnotes",
            mpn=instance.get("mpn"),
            destination_directory=destination_directory,
            used_rev=None,
            item_name=instance_name
        )

        # === Replace placeholder in SVG ===
        drawing_path = os.path.join(destination_directory, f"{instance_name}-drawing.svg")
        if not os.path.exists(drawing_path):
            print(f"[WARN] Drawing not found: {drawing_path}")
            continue

        with open(drawing_path, 'r', encoding='utf-8') as f:
            svg = f.read()

        svg = re.sub(r'>flagnote-text<', f'>{instance.get("bubble_text")}<', svg)

        with open(drawing_path, 'w', encoding='utf-8') as f:
            f.write(svg)

def compile_buildnotes():
    # add buildnote itemtypes to list (separate from the flagnote itemtype) to form source of truth for the list itself
    for instance in instances_list.read_instance_rows():
        if instance.get("item_type") == "Flagnote" and instance.get("note_type") == "buildnote":
            buildnote_text = instance.get("note_text")

            # does this buildnote exist as an instance yet?
            already_exists = False
            for instance2 in instances_list.read_instance_rows():
                if instance2.get("item_type") == "Buildnote" and instance2.get("note_text") == buildnote_text:
                    already_exists = True
            
            # if not, make it
            if already_exists == False:
                instances_list.add_unless_exists(f"buildnote-{instance.get("bubble_text")}", {
                    "item_type": "Buildnote",
                    "note_text": buildnote_text
                })