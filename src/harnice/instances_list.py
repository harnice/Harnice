import yaml
import json
import csv
from collections import defaultdict
import os
import math
from harnice import (
    fileio
)

RECOGNIZED_ITEM_TYPES = {
    "Segment",
    "Node",
    "Flagnote",
    "Flagnote leader",
    "Location"
}

INSTANCES_LIST_COLUMNS = [
    'instance_name',
    'print_name',
    'bom_line_number',
    'mpn',
    'item_type',
    'parent_instance', #<--------- change to functional_parent
    'location_is_node_or_segment',
    'parent_csys', #<----------- change to parent_csys_instance
    'parent_csys_name', #<----------- add
    'circuit_id',
    'circuit_id_port',
    'length',
    'diameter', #<---------- change to print_diameter
    'node_at_end_a',
    'node_at_end_b',
    'translate_x',
    'translate_y',
    'rotate_csys',
    'absolute_rotation',
    'note_type',
    'note_number', #<--------- merge with parent_csys and import instances of child csys?
    'bubble_text',
    'supplier',
    'lib_latest_rev',
    'lib_rev_used_here',
    'lib_status',
    'lib_datemodified',
    'lib_datereleased',
    'lib_drawnby'
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

def add(instance_name, instance_data):
    """
    Adds a new instance to the instances list TSV.

    Args:
        instance_name (str): The name of the instance to add.
        instance_data (dict): Dictionary of instance attributes. May include "instance_name".

    Raises:
        ValueError: If instance_name is missing, already exists, or conflicts with instance_data["instance_name"].
    
    Behavior:
        - Raises ValueError if an instance with the same instance_name already exists.
        - Raises ValueError if instance_name and instance_data["instance_name"] disagree.
        - Only writes fields defined in INSTANCES_LIST_COLUMNS.
        - Missing fields are written as empty strings.
    """
    if not instance_name:
        raise ValueError("Missing required argument: 'instance_name'")

    if "instance_name" in instance_data and instance_data["instance_name"] != instance_name:
        raise ValueError(f"Inconsistent instance_name: argument='{instance_name}' vs data['instance_name']='{instance_data['instance_name']}'")

    instance_data["instance_name"] = instance_name  # Ensure the dict includes the name

    instances = read_instance_rows()
    if any(row.get("instance_name") == instance_name for row in instances):
        raise ValueError(f"Instance already exists: '{instance_name}'")

    with open(fileio.path('instances list'), 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=INSTANCES_LIST_COLUMNS, delimiter='\t')
        writer.writerow({key: instance_data.get(key, '') for key in INSTANCES_LIST_COLUMNS})

def add_unless_exists(instance_name, instance_data):
    """
    Adds an instance to the instances list unless an instance with the same name already exists.

    Args:
        instance_name (str): The name of the instance to add.
        instance_data (dict): Dictionary of instance attributes. May include "instance_name".

    Raises:
        ValueError: If instance_name is missing, or if instance_name and instance_data["instance_name"] disagree.
    """
    if not instance_name:
        raise ValueError("Missing required argument: 'instance_name'")

    if "instance_name" in instance_data and instance_data["instance_name"] != instance_name:
        raise ValueError(f"Inconsistent instance_name: argument='{instance_name}' vs data['instance_name']='{instance_data['instance_name']}'")

    instance_data["instance_name"] = instance_name  # Ensure consistency

    instances = read_instance_rows()
    if not any(inst.get("instance_name") == instance_name for inst in instances):
        add(instance_name, instance_data)

def modify(instance_name, instance_data):
    """
    Modifies an existing instance in the instances list TSV.

    Args:
        instance_name (str): The name of the instance to modify.
        instance_data (dict): A dictionary of fieldnames and new values to update.

    Raises:
        ValueError: If the instance is not found, or if instance_name conflicts with instance_data["instance_name"].
    """
    # Sanity check: ensure instance_name is consistent
    if "instance_name" in instance_data:
        if instance_data["instance_name"] != instance_name:
            raise ValueError(f"Mismatch between argument instance_name ('{instance_name}') "
                             f"and instance_data['instance_name'] ('{instance_data['instance_name']}').")
    else:
        instance_data["instance_name"] = instance_name

    path = fileio.path("instances list")

    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        rows = list(reader)
        fieldnames = reader.fieldnames

    modified = False
    for row in rows:
        if row.get("instance_name") == instance_name:
            row.update(instance_data)
            modified = True
            break

    if not modified:
        raise ValueError(f"Instance '{instance_name}' not found in the instances list.")

    with open(path, "w", newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter='\t')
        writer.writeheader()
        writer.writerows(rows)

def make_new_list():
    write_instance_rows([])

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

def add_revhistory_of_imported_part(instance_name, rev_data):
    # Expected rev_data is a dict with keys from REVISION_HISTORY_COLUMNS
    with open(fileio.path("instances list"), newline='') as f:
        reader = csv.DictReader(f, delimiter='\t')
        rows = list(reader)
        fieldnames = reader.fieldnames

    for row in rows:
        if row.get("instance_name") == instance_name:
            row["lib_latest_rev"] = str(rev_data.get("rev", ""))
            row["lib_rev_used_here"] = str(rev_data.get("rev", ""))
            row["lib_status"] = rev_data.get("status", "")
            row["lib_datemodified"] = rev_data.get("datemodified", "")
            row["lib_datereleased"] = rev_data.get("datereleased", "")
            row["lib_drawnby"] = rev_data.get("drawnby", "")
            break  # instance_name is unique

    with open(fileio.path("instances list"), "w", newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter='\t')
        writer.writeheader()
        writer.writerows(rows)

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
        note_type = row.get("note_type","").strip()

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
            "absolute_rotation": "",
            "note_type": note_type
        }
        append_instance_row(location_instance)

        # === Step 6: Append leader instance ===
        flagnote_instance = {
            "instance_name": f"{instance_name}-leader",
            "bom_line_number": "",
            "mpn": "",
            "item_type": "Flagnote leader",
            "parent_instance": affected,
            "parent_csys": parent_csys,
            "supplier": "",
            "lib_latest_rev": "",
            "lib_rev_used_here": "",
            "length": "",
            "diameter": "",
            "translate_x": "",
            "translate_y": "",
            "rotate_csys": "",
            "absolute_rotation": "",
            "note_number": note_number,
            "bubble_text": "",
            "note_type": note_type
        }
        append_instance_row(flagnote_instance)

        # === Step 7: Append flagnote instance ===
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
            "bubble_text": bubble_text,
            "note_type": note_type
        }
        append_instance_row(flagnote_instance)

def instance_names_of_adjacent_ports(target_instance):
    for instance in read_instance_rows():
        if instance.get("instance_name") == target_instance:
            #assign parents to contacts based on the assumption that one of the two adjacent items in the circuit will be a node-item
            if instance.get("circuit_id") == "" or instance.get("circuit_id_port") == "":
                raise ValueError(f"Circuit order unspecified for {target_instance}")

            circuit_id = instance.get("circuit_id")
            circuit_id_port = int(instance.get("circuit_id_port"))

            #find the adjacent port
            prev_port = ""
            next_port = ""

            for instance2 in read_instance_rows():
                if instance2.get("circuit_id") == circuit_id:
                    if int(instance2.get("circuit_id_port")) == circuit_id_port - 1:
                        prev_port = instance2.get("instance_name")
                    if int(instance2.get("circuit_id_port")) == circuit_id_port + 1:
                        next_port = instance2.get("instance_name")
            
            return prev_port, next_port

def attribute_of(target_instance, attribute):
    for instance in read_instance_rows():
        if instance.get("instance_name") == target_instance:
            return instance.get(attribute)

def recursive_parent_search(start_instance, parent_type, attribute_name, wanted_attribute_value):
    wanted_instance = start_instance

    while not attribute_of(wanted_instance, attribute_name) == wanted_attribute_value:
        wanted_instance = attribute_of(wanted_instance, parent_type)
        if wanted_instance == "" or wanted_instance == None:
            raise ValueError(
                f"Instance with '{attribute_name}' equal to '{wanted_attribute_value}' not found in the {parent_type} lineage of instance {start_instance}"
            )

    return wanted_instance

"""
template instances list modifier:
def example_instances_list_function():
    instances = read_instance_rows()
    for instance in instances:
        # do stuff
        # instance.get()
    write_instance_rows(instances)
"""