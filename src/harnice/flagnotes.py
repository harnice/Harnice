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
    "action",
    "note_type",
    "note",
    "shape",
    "shape_supplier",
    "bubble_text",
    "affectedinstances"
]

AUTO_FLAGNOTES_COLUMNS = [
    "note_type",
    "note",
    "shape",
    "shape_supplier",
    "bubble_text",
    "affectedinstances"
]

BUILDNOTES_COLUMNS = [
    "buildnote_number",
    "note",
    "has_shape",
    "shape",
    "shape_supplier"
]

def ensure_manual_list_exists():
    if not os.path.exists(fileio.path('flagnotes manual')):
        with open(fileio.path('flagnotes manual'), 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=MANUAL_FLAGNOTES_COLUMNS, delimiter='\t')
            writer.writeheader()

def compile_all_flagnotes():
    # === Step 1: Reset "flagnotes list" ===
    with open(fileio.path('flagnotes list'), 'w', newline='', encoding='utf-8') as f_flag:
        writer = csv.DictWriter(f_flag, fieldnames=AUTO_FLAGNOTES_COLUMNS, delimiter='\t')
        writer.writeheader()

    # === Step 2: Read and normalize manual flagnote rows ===
    manual_rows = []
    buildnote_counter = 1

    if os.path.exists(fileio.path('flagnotes manual')):
        with open(fileio.path('flagnotes manual'), newline='', encoding='utf-8') as f_manual:
            reader = csv.DictReader(f_manual, delimiter='\t')
            for row in reader:
                normalized_row = {column: row.get(column, "").strip() for column in AUTO_FLAGNOTES_COLUMNS}
                note_type = normalized_row.get("note_type", "")

                if note_type == "buildnote":
                    if not normalized_row.get("bubble_text"):
                        normalized_row["bubble_text"] = str(buildnote_counter)
                        buildnote_counter += 1
                    else:
                        try:
                            int(normalized_row["bubble_text"])
                        except ValueError:
                            raise ValueError(f"Non-numeric bubble_text: {normalized_row['bubble_text']}")

                manual_rows.append(normalized_row)

    # === Step 3: Generate revision flagnote rows from revision history ===
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

    # === Step 4: Generate auto flagnote rows from instance list ===
    auto_generated_rows = []
    instances = instances_list.read_instance_rows()
    for instance in instances:
        item_type = instance.get("item_type", "").strip()
        instance_name = instance.get("instance_name", "").strip()
        if item_type in {"Connector", "Backshell"}:
            auto_generated_rows.append({
                "note_type": "part_name",
                "note": "",
                "shape": "part_name",
                "shape_supplier": "public",
                "bubble_text": instance_name,
                "affectedinstances": instance_name
            })
            auto_generated_rows.append({
                "note_type": "bom_item",
                "note": "",
                "shape": "bom_item",
                "shape_supplier": "public",
                "bubble_text": instance.get("bom_line_number", "").strip(),
                "affectedinstances": instance_name
            })

    # === Step 5: Combine all flagnote rows ===
    all_rows = manual_rows + revision_rows + auto_generated_rows

    # === Step 6: Expand rows with multiple affected instances ===
    expanded_rows = []
    for row in all_rows:
        affected_field = row.get('affectedinstances', '').strip()
        affected_instances = [i.strip() for i in affected_field.split(',') if i.strip()] or ['']
        for instance in affected_instances:
            new_row = row.copy()
            new_row['affectedinstances'] = instance
            expanded_rows.append(new_row)

    # === Step 7: Sort rows by note_type priority and affected instance ===
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

    # === Step 8: Assign bubble_text for non-buildnotes if still missing ===
    bubble_counters = {}
    for row in expanded_rows:
        note_type = row.get("note_type", "").strip()
        if note_type == "buildnote":
            continue  # already assigned during manual row processing

        instance = row.get("affectedinstances", "").strip()
        bubble_text = row.get("bubble_text", "").strip()
        fallback_scope = row.get("note", "").strip()
        key = (note_type, instance or fallback_scope)

        if not bubble_text:
            bubble_counters[key] = bubble_counters.get(key, 0)
            row["bubble_text"] = str(bubble_counters[key])
            bubble_counters[key] += 1

    # === Step 9: Write all rows to flagnotes list ===
    with open(fileio.path('flagnotes list'), 'a', newline='', encoding='utf-8') as f_flag:
        writer = csv.DictWriter(f_flag, fieldnames=AUTO_FLAGNOTES_COLUMNS, delimiter='\t')
        writer.writerows(expanded_rows)

    # === Step 10: Derive buildnotes list from final flagnotes list ===
    buildnote_seen = {}
    buildnote_rows = []

    with open(fileio.path('flagnotes list'), newline='', encoding='utf-8') as f_flag:
        reader = csv.DictReader(f_flag, delimiter='\t')
        for row in reader:
            if row.get("note_type", "").strip() != "buildnote":
                continue

            buildnote_number = row.get("bubble_text", "").strip()
            if buildnote_number in buildnote_seen:
                continue

            buildnote_seen[buildnote_number] = True

            buildnote_rows.append({
                "buildnote_number": buildnote_number,
                "note": row.get("note", "").strip(),
                "has_shape": "True" if row.get("shape", "").strip() else "False",
                "shape": row.get("shape", "").strip(),
                "shape_supplier": row.get("shape_supplier", "").strip(),
            })

    buildnote_rows.sort(key=lambda row: int(row.get("buildnote_number", 0)))

    with open(fileio.path('buildnotes list'), 'w', newline='', encoding='utf-8') as f_build:
        writer = csv.DictWriter(f_build, fieldnames=BUILDNOTES_COLUMNS, delimiter='\t')
        writer.writeheader()
        writer.writerows(buildnote_rows)

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
                if parent_type in instances_list.editable_component_types():
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
                arrow_len = 6  # px
                arrow_width = 4  # px

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
                        <line x1="{from_x:.2f}" y1="{from_y:.2f}" x2="{to_x:.2f}" y2="{to_y:.2f}" stroke="black" stroke-width="1" />
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
