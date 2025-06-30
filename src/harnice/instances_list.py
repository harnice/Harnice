import yaml
import json
import csv
from collections import defaultdict
import os
import math
from harnice import (
    fileio
)

INSTANCES_LIST_COLUMNS = [
    'instance_name',
    'bom_line_number',
    'mpn',
    'item_type',
    'parent_instance',
    'parent_csys',
    'supplier',
    'lib_latest_rev',
    'lib_rev_used_here',
    'length',
    'diameter',
    'translate_x',
    'translate_y',
    'rotate_csys',
    'absolute_rotation',
    'note_number',
    'bubble_text'
]

def load_yaml_data():
    with open(fileio.path('harness yaml'), 'r') as file:
        return yaml.safe_load(file)

def read_instance_rows():
    with open(fileio.path('instances list'), newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f, delimiter='\t'))

def write_instance_rows(rows):
    with open(fileio.path('instances list'), 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=INSTANCES_LIST_COLUMNS, delimiter='\t')
        writer.writeheader()
        writer.writerows(rows)

def append_instance_row(data_dict):
    with open(fileio.path('instances list'), 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=INSTANCES_LIST_COLUMNS, delimiter='\t')
        writer.writerow({key: data_dict.get(key, '') for key in INSTANCES_LIST_COLUMNS})

def make_new_list():
    write_instance_rows([])

def add_connectors():
    yaml_data = load_yaml_data()
    for instance_name, connector in yaml_data.get('connectors', {}).items():
        for component in connector.get('additional_components', []):
            suffix = 'bs' if component.get('type', '').lower() == 'backshell' else component.get('type', '').lower()
            component_instance = f"{instance_name}.{suffix}"
            append_instance_row({
                'instance_name': component_instance,
                'mpn': component.get('mpn', ''),
                'item_type': component.get('type', ''),
                'parent_instance': instance_name,
                'supplier': component.get('supplier', '')
            })

        append_instance_row({
            'instance_name': instance_name,
            'mpn': connector.get('mpn', ''),
            'item_type': 'Connector',
            'parent_instance': instance_name, #needed to find parent csys
            'supplier': connector.get('supplier', '')
        })

def add_cables():
    yaml_data = load_yaml_data()
    for cable_name, cable in yaml_data.get('cables', {}).items():
        append_instance_row({
            'instance_name': cable_name,
            'mpn': cable.get('mpn', ''),
            'item_type': 'Cable',
            'supplier': cable.get('supplier', '')
        })

def add_cable_lengths():
    with open(fileio.path('connections to graph'), 'r') as json_file:
        graph_data = json.load(json_file)

    instances = read_instance_rows()
    for instance in instances:
        if instance.get('item_type', '').lower() == 'cable':
            instance['length'] = graph_data.get(instance['instance_name'], {}).get('total_length', '')

    write_instance_rows(instances)

def convert_to_bom():
    rows = read_instance_rows()
    mpn_groups = defaultdict(lambda: {'qty': 0, 'item_type': '', 'supplier': '', 'total_length': 0.0})

    for row in rows:
        mpn = row.get('mpn', '').strip()
        if not mpn:
            continue
        group = mpn_groups[mpn]
        group['qty'] += 1
        group['item_type'] = row.get('item_type', '')
        group['supplier'] = row.get('supplier', '')
        if group['item_type'].lower() == 'cable':
            try:
                group['total_length'] += float(row.get('length', '') or 0)
            except ValueError:
                pass

    output = []
    for i, (mpn, group) in enumerate(mpn_groups.items(), 1):
        row = {
            'bom_line_number': i,
            'mpn': mpn,
            'item_type': group['item_type'],
            'qty': group['qty'],
            'supplier': group['supplier']
        }
        if group['item_type'].lower() == 'cable':
            row['total_length_exact'] = f"{group['total_length']:.2f}"
        output.append(row)

    fieldnames = ['bom_line_number', 'mpn', 'item_type', 'qty', 'supplier', 'total_length_exact']
    with open(fileio.path('harness bom'), 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter='\t', extrasaction='ignore')
        writer.writeheader()
        writer.writerows(output)

    return fileio.path('harness bom')

def add_bom_line_numbers():
    with open(fileio.path('harness bom'), newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        mpn_map = {row['mpn']: row['bom_line_number'] for row in reader if row.get('mpn')}

    rows = read_instance_rows()
    for row in rows:
        row['bom_line_number'] = mpn_map.get(row.get('mpn', ''), '')

    write_instance_rows(rows)
    return fileio.path('instances list')

def add_nodes():
    with open(fileio.path('formboard graph definition'), 'r') as f:
        graph = yaml.safe_load(f)

    node_set = set()
    for seg in graph.values():
        node_set.update([seg.get('segment_end_a'), seg.get('segment_end_b')])

    for node in sorted(filter(None, node_set)):
        append_instance_row({
            'instance_name': node,
            'item_type': 'Node',
            'parent_instance': node
        })

def add_lib_latest_rev(instance_name, rev):
    with open(fileio.path("instances list"), newline='') as f:
        reader = csv.DictReader(f, delimiter='\t')
        rows = list(reader)
        fieldnames = reader.fieldnames

    for row in rows:
        if row.get("instance_name") == instance_name:
            row["lib_latest_rev"] = str(rev)
            break  # assume instance_name is unique

    with open(fileio.path("instances list"), "w", newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter='\t')
        writer.writeheader()
        writer.writerows(rows)

def add_lib_used_rev(instance_name, rev):
    with open(fileio.path("instances list"), newline='') as f:
        reader = csv.DictReader(f, delimiter='\t')
        rows = list(reader)
        fieldnames = reader.fieldnames

    for row in rows:
        if row.get("instance_name") == instance_name:
            row["lib_rev_used_here"] = str(rev)
            break  # assume instance_name is unique

    with open(fileio.path("instances list"), "w", newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter='\t')
        writer.writeheader()
        writer.writerows(rows)

def update_parent_csys():
    instances = read_instance_rows()
    instance_lookup = {inst.get('instance_name'): inst for inst in instances}

    for instance in instances:
        instance_name = instance.get('instance_name', '').strip()
        if not instance_name:
            continue

        # Build the path to the attributes JSON file
        attributes_path = os.path.join(
            fileio.dirpath("editable_instance_data"),
            instance_name,
            f"{instance_name}-attributes.json"
        )

        # Skip if the attributes file does not exist
        if not os.path.exists(attributes_path):
            continue

        # Load the attributes JSON
        try:
            with open(attributes_path, 'r', encoding='utf-8') as f:
                attributes_data = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            continue  # Skip invalid or missing JSON

        # Get csys_parent_prefs from attributes
        csys_parent_prefs = attributes_data.get("plotting_info", {}).get("csys_parent_prefs", [])

        # Iterate through parent preferences
        for pref in csys_parent_prefs:
            candidate_name = f"{instance.get("parent_instance")}{pref}"
            if candidate_name in instance_lookup:
                instance['parent_csys'] = candidate_name
                break  # Found a match, exit early
        # If no match, do nothing (parent_csys remains unchanged)

    write_instance_rows(instances)

def update_component_translate():
    instances = read_instance_rows()
    for instance in instances:
        instance_name = instance.get('instance_name', '').strip()
        if not instance_name:
            continue

        attributes_path = os.path.join(
            fileio.dirpath("editable_instance_data"),
            instance_name,
            f"{instance_name}-attributes.json"
        )

        if not os.path.exists(attributes_path):
            continue

        try:
            with open(attributes_path, "r", encoding="utf-8") as f:
                attributes_data = json.load(f)
        except (json.JSONDecodeError, IOError):
            continue

        component_translate = (
            attributes_data
            .get("plotting_info", {})
            .get("component_translate_inches", {})
        )

        if component_translate:
            instance['translate_x'] = str(component_translate.get('translate_x', ''))
            instance['translate_y'] = str(component_translate.get('translate_y', ''))
            instance['rotate_csys'] = str(component_translate.get('rotate_csys', ''))

    write_instance_rows(instances)

def generate_nodes_from_connectors():
    instances = read_instance_rows()

    #Append a new '.node' child row
    for instance in instances:
        if instance.get('item_type') == "Connector":
            append_instance_row({
                'instance_name': instance.get('instance_name') + ".node",
                'item_type': 'Node',
                'parent_instance': instance.get('instance_name'),
            })

def add_nodes_from_formboard():
    instances = read_instance_rows()

    try:
        with open(fileio.path("formboard graph definition"), "r") as f:
            formboard_data = json.load(f)
    except FileNotFoundError:
        print(f"Warning: Formboard definition file not found at {fileio.name('formboard graph definition')}")
        formboard_data = {}

    # Find all nodes already defined in formboard
    nodes_in_formboard = set()
    for segment in formboard_data.values():
        nodes_in_formboard.add(segment.get('segment_end_a', ''))
        nodes_in_formboard.add(segment.get('segment_end_b', ''))
    nodes_in_formboard.discard('')

    # Collect all known instance names for lookup
    existing_instance_names = {instance.get('instance_name', '') for instance in instances}

    # Add any node from formboard that's missing in instances list
    for node_name in nodes_in_formboard:
        if node_name and node_name not in existing_instance_names:
            instances.append({
                'instance_name': node_name,
                'item_type': 'Node',
            })

    write_instance_rows(instances)

def add_segments_from_formboard():
    instances = read_instance_rows()

    try:
        with open(fileio.path("formboard graph definition"), "r") as f:
            formboard_data = json.load(f)
    except FileNotFoundError:
        print(f"Warning: Formboard definition file not found at {fileio.name('formboard graph definition')}")
        formboard_data = {}

    # Gather all existing instance names to avoid duplicates
    existing_instance_names = {inst.get('instance_name', '') for inst in instances}

    # Append segments that are missing in the instances list
    for segment_name, segment in formboard_data.items():
        if segment_name not in existing_instance_names:
            instances.append({
                'instance_name': segment_name,
                'item_type': 'Segment',
                'length': str(segment.get('length', '')),
                'diameter': str(segment.get('diameter', '')),
                'parent_csys': str(segment.get('segment_end_a', '')),
            })

    write_instance_rows(instances)


def parent(instance_name):
    instances = read_instance_rows()
    for instance in instances:
        if instance.get('instance_name') == instance_name:
            print(f" for known child: {instance.get('instance_name')}")
            print(f"returning parent: {instance.get('parent_instance')}")
            return instance.get('parent_instance')

def add_angles_to_nodes():
    #open formboard definition file
    #for each instance in instances list:
        #if item type == Node:
            #average_angle = 0
            #angle_counter = 0
            #for each time instance_name is found as a node of a segment within formboard definition:
                #average_angle += angle of segment
                #angle_counter += 1
            #average_angle = average_angle / angle_counter
            #store average_angle into field 'rotate_csys' of instances list

    #write instances list

    # Load formboard graph definition
    with open(fileio.path("formboard graph definition"), "r") as f:
        formboard_data = json.load(f)

    # Read instances list
    instances = read_instance_rows()
    instance_lookup = {row['instance_name']: row for row in instances}

    # For each Node, compute average angle
    for instance in instances:
        if instance.get("item_type") != "Node":
            continue

        instance_name = instance.get("instance_name", "")
        total_angle = 0
        count = 0

        for segment in formboard_data.values():
            if segment.get("segment_end_a") == instance_name or segment.get("segment_end_b") == instance_name:
                angle = segment.get("angle")
                if segment.get("segment_end_a") == instance_name:
                    angle += 180
                if isinstance(angle, (int, float)):
                    total_angle += angle 
                    count += 1
                #flip influences from the A side of each segment

        if count > 0:
            average_angle = round(total_angle / count, 2)
            instance["rotate_csys"] = str(average_angle)
        else:
            instance["rotate_csys"] = ""

        #keep it to 360 deg
        while total_angle >= 360:
            total_angle -= 360

    write_instance_rows(instances)

def add_absolute_angles_to_segments():
    # Load formboard graph definition
    with open(fileio.path("formboard graph definition"), "r") as f:
        formboard_data = json.load(f)

    # Read instances list
    instances = read_instance_rows()

    # For each Segment instance, add the angle to the instances list
    for instance in instances:
        if instance.get("item_type") == "Segment":
            instance_name = instance.get("instance_name", "")
            segment_data = formboard_data.get(instance_name, {})
            angle = segment_data.get("angle", "")
            instance["absolute_rotation"] = str(angle) if angle != "" else ""

    write_instance_rows(instances)

def add_flagnotes():
    # === Step 1: Load existing instance rows ===
    instances = read_instance_rows()
    instance_lookup = {inst.get("instance_name", "").strip(): inst for inst in instances}

    # === Step 2: Read flagnotes list ===
    with open(fileio.path("flagnotes list"), newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        flagnote_rows = list(reader)

    # === Step 3: Group and number flagnotes per affected instance ===
    note_counters = {}  # {affected: current_note_number}

    for row in flagnote_rows:
        affected = row.get("affectedinstances", "").strip()
        bubble_text = row.get("bubble_text", "").strip()
        if not affected:
            continue

        note_number = note_counters.get(affected, 0)
        note_counters[affected] = note_number + 1
        instance_name = f"{affected}-flagnote{note_number}"

        # Determine parent_csys from the original instance
        parent_csys = instance_lookup.get(affected, {}).get("parent_csys", "")

        # === Step 4: Try to load flagnote location from JSON ===
        translate_x = ""
        translate_y = ""
        attr_path = os.path.join(fileio.dirpath("editable_instance_data"), affected, f"{affected}-attributes.json")

        try:
            with open(attr_path, 'r', encoding='utf-8') as f_json:
                data = json.load(f_json)
                locs = data.get("flagnote_locations", [])
                if note_number < len(locs):
                    loc = locs[note_number]
                    angle_rad = math.radians(loc.get("angle", 0))
                    distance = loc.get("distance", 0)
                    translate_x = round(math.cos(angle_rad) * distance, 5)
                    translate_y = round(math.sin(angle_rad) * distance, 5)
        except Exception as e:
            print(f"[WARN] Could not read location data for {instance_name}: {e}")

        # === Step 5: Append location instance ===
        location_instance = {
            "instance_name": f"{instance_name}-location",
            "bom_line_number": "",
            "mpn": "",
            "item_type": "Flagnote location",
            "parent_instance": affected,
            "parent_csys": parent_csys,
            "supplier": "",
            "lib_latest_rev": "",
            "lib_rev_used_here": "",
            "length": "",
            "diameter": "",
            "translate_x": translate_x,
            "translate_y": translate_y,
            "rotate_csys": "",
            "note_number": note_number,
            "absolute_rotation": ""
        }
        append_instance_row(location_instance)

        # === Step 6: Append flagnote instance ===
        flagnote_instance = {
            "instance_name": instance_name,
            "bom_line_number": "",
            "mpn": row.get("shape", "").strip(),
            "item_type": "Flagnote",
            "parent_instance": affected,
            "parent_csys": f"{instance_name}-location",
            "supplier": row.get("shape_supplier", "").strip(),
            "lib_latest_rev": "",
            "lib_rev_used_here": "",
            "length": "",
            "diameter": "",
            "translate_x": 0,
            "translate_y": 0,
            "rotate_csys": "",
            "absolute_rotation": 0,
            "note_number": note_number,
            "bubble_text": bubble_text
        }
        append_instance_row(flagnote_instance)

        # === Step 7: Append leader instance ===
        flagnote_instance = {
            "instance_name": f"{instance_name}-leader",
            "bom_line_number": "",
            "mpn": "",
            "item_type": "Flagnote leader",
            "parent_instance": affected,
            "parent_csys": f"{instance_name}-location",
            "supplier": "",
            "lib_latest_rev": "",
            "lib_rev_used_here": "",
            "length": "",
            "diameter": "",
            "translate_x": "",
            "translate_y": "",
            "rotate_csys": "",
            "absolute_rotation": "",
            "note_number": "",
            "bubble_text": ""
        }
        append_instance_row(flagnote_instance)

"""
template instances list modifier:
def example_instances_list_function():
    instances = read_instance_rows()
    for instance in instances:
        # do stuff
        # instance.get()
    write_instance_rows(instances)
"""