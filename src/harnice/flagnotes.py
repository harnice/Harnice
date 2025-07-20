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
    "note",
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
        fileio.dirpath("editable_instance_data"),
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

    # === Load all rows from flagnotes list into memory ===
    with open(fileio.path("flagnotes list"), newline='', encoding='utf-8') as f:
        flagnotes_list = list(csv.DictReader(f, delimiter='\t'))

    for instance in instances:
        if instance.get("item_type", "").lower() != "flagnote":
            continue

        instance_name = instance.get("instance_name")
        parent_instance = instance.get("parent_instance", "").strip()

        destination_directory = os.path.join(fileio.dirpath("uneditable_instance_data"), instance_name)
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

def make_leader_drawings():
    instances = instances_list.read_instance_rows()

    formboards = []
    with open(fileio.path("harnice output contents"), 'r') as f:
        page_setup = json.load(f)
        formboards = page_setup.get("formboards", [])

    for formboard in formboards:
        scale_name = page_setup.get("formboards", []).get(formboard, []).get('scale', "")
        scale = page_setup.get("scales", []).get(scale_name, "")

        for instance in instances:
            if instance.get("item_type") == "Flagnote leader":

                leader_name = instance.get("instance_name")
                leader_parent = instance.get("parent_instance")
                flagnote_number = int(instance.get("note_number", "0"))
                parent_attributes_file = ""

                # Find the instance that matches `leader_parent`
                parent_type = ""
                for instance2 in instances:
                    if instance2.get("instance_name") == leader_parent:
                        parent_type = instance2.get("item_type", "")
                        break

                # Then decide path based on its type
                if parent_type not in instances_list.RECOGNIZED_ITEM_TYPES:
                    parent_attributes_file = os.path.join(fileio.dirpath("editable_instance_data"), leader_parent, f"{leader_parent}-attributes.json")
                else:
                    parent_attributes_file = os.path.join(fileio.dirpath("uneditable_instance_data"), leader_parent, f"{leader_parent}-attributes.json")

                if not os.path.exists(parent_attributes_file):
                    print(f"[WARN] Missing attributes for parent: {parent_attributes_file}")
                    continue

                with open(parent_attributes_file, encoding='utf-8') as f:
                    attr_data = json.load(f)

                flagnote_locations = attr_data.get("flagnote_locations", [])
                if flagnote_number >= len(flagnote_locations):
                    print(f"[WARN] flagnote_number {flagnote_number} out of range for {parent_instance}")
                    continue

                loc = flagnote_locations[flagnote_number]
                angle = math.radians(float(loc.get("angle")))
                distance = float(loc.get("distance"))

                arrowhead_angle_raw = loc.get("arrowhead_angle")
                arrowhead_angle = angle if arrowhead_angle_raw == "" else math.radians(float(arrowhead_angle_raw))
                arrowhead_distance = float(loc.get("arrowhead_distance"))

                # === Convert from inches to pixels (96 dpi) ===
                from_x = math.cos(angle) * distance * 96
                from_y = -math.sin(angle) * distance * 96
                to_x = math.cos(arrowhead_angle) * arrowhead_distance * 96
                to_y = -math.sin(arrowhead_angle) * arrowhead_distance * 96

                # === Arrowhead geometry (manual triangle) ===
                arrow_len = 6 / scale # px
                arrow_width = 4 / scale # px

                dx = to_x - from_x
                dy = to_y - from_y
                mag = math.hypot(dx, dy)
                ux, uy = dx / mag, dy / mag
                px, py = -uy, ux  # perpendicular to direction

                tip = (to_x, to_y)
                base1 = (to_x - arrow_len * ux + arrow_width * px / 2,
                        to_y - arrow_len * uy + arrow_width * py / 2)
                base2 = (to_x - arrow_len * ux - arrow_width * px / 2,
                        to_y - arrow_len * uy - arrow_width * py / 2)

                arrow_points = f"{tip[0]:.2f},{tip[1]:.2f} {base1[0]:.2f},{base1[1]:.2f} {base2[0]:.2f},{base2[1]:.2f}"

                # === SVG content ===
                svg_content = f'''
                <svg xmlns="http://www.w3.org/2000/svg" width="384" height="384" viewBox="0 0 384 384">
                    <g id="{instance.get("instance_name")}-contents-start">
                        <line x1="{from_x:.2f}" y1="{from_y:.2f}" x2="{to_x:.2f}" y2="{to_y:.2f}" stroke="black" stroke-width="{1/scale:.2f}" />
                        <polygon points="{arrow_points}" fill="black" />
                    </g>
                    <g id="{instance.get("instance_name")}-contents-end"></g>
                </svg>
                '''

                leader_dir = os.path.join(fileio.dirpath("uneditable_instance_data"), formboard, leader_name)
                os.makedirs(leader_dir, exist_ok=True)

                output_filename = os.path.join(leader_dir, f"{leader_name}-drawing.svg")
                with open(output_filename, 'w') as svg_file:
                    svg_file.write(svg_content)
