import json
import os
import random
import math
import csv
from collections import defaultdict, deque
from harnice import (
    instances_list,
    fileio
)

FORMBOARD_TSV_COLUMNS = [
    "segment_id",
    "node_at_end_a",
    "node_at_end_b",
    "length",
    "angle",
    "diameter"
]

def read_segment_rows():
    """
    Reads all rows from the formboard graph definition TSV.

    Returns:
        List[dict]: Each row as a dictionary with keys from FORMBOARD_TSV_COLUMNS.
    """
    with open(fileio.path('formboard graph definition'), newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f, delimiter='\t'))

def write_segment_rows(rows):
    """
    Overwrites the formboard graph definition TSV with the provided rows.

    Args:
        rows (List[dict]): List of dictionaries matching FORMBOARD_TSV_COLUMNS.
    """
    with open(fileio.path('formboard graph definition'), 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=FORMBOARD_TSV_COLUMNS, delimiter='\t')
        writer.writeheader()
        writer.writerows(rows)

def append_segment_row(data_dict):
    """
    Appends a single row to the formboard graph definition TSV.

    Args:
        data_dict (dict): Dictionary of segment data.
                          Missing fields will be written as empty strings.
    """
    with open(fileio.path('formboard graph definition'), 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=FORMBOARD_TSV_COLUMNS, delimiter='\t')
        writer.writerow({key: data_dict.get(key, '') for key in FORMBOARD_TSV_COLUMNS})

def add_segment_to_formboard_def(segment_id, segment_data):
    if not segment_id:
        raise ValueError("Missing required argument: 'segment_id'")

    if "segment_id" in segment_data and segment_data["segment_id"] != segment_id:
        raise ValueError(f"Inconsistent segment_id: argument='{segment_id}' vs data['segment_id']='{segment_data['segment_id']}'")

    segment_data["segment_id"] = segment_id  # Ensure it is included

    existing = read_segment_rows()
    if any(row.get("segment_id") == segment_id for row in existing):
        raise ValueError(f"Segment already exists: '{segment_id}'")

    append_segment_row(segment_data)

def segment_attribute_of(segment_id, key):
    """
    Returns the value of the specified attribute for the given segment.

    Args:
        segment_id (str): The ID of the segment to look up.
        key (str): The attribute name to retrieve.

    Returns:
        str or None: The value of the attribute, or None if not found.
    """
    for row in read_segment_rows():
        if row.get("segment_id") == segment_id:
            return row.get(key)
    return None

def validate_nodes():
    # Ensure TSV exists
    if not os.path.exists(fileio.name("formboard graph definition")):
        with open(fileio.name("formboard graph definition"), 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, delimiter='\t', fieldnames=FORMBOARD_TSV_COLUMNS)
            writer.writeheader()

    # Collect node names from the instance list
    nodes_from_instances_list = {
        instance.get("instance_name")
        for instance in instances_list.read_instance_rows()
        if instance.get("item_type") == "Node"
    }

    # Extract nodes already involved in segments in formboard definition
    nodes_from_formboard_definition = set()
    for row in read_segment_rows():
        nodes_from_formboard_definition.add(row.get("node_at_end_a", ""))
        nodes_from_formboard_definition.add(row.get("node_at_end_b", ""))
    nodes_from_formboard_definition.discard("")

    # --- Case 1: No segments exist in formboard definition yet, build from scratch ---
    if not read_segment_rows():
        #if there are 3 or more nodes already defined by the instances list (probably by a connector or something)
        if len(nodes_from_instances_list) > 2:
            #add a center origin node
            origin_node = "node1"
            node_counter = 0
            #add one segment per node connecting to the origin node
            for instance in instances_list.read_instance_rows():
                if instance.get("item_type") == "Node":
                    segment_id = instance.get("instance_name") + "_leg"
                    add_segment_to_formboard_def(segment_id, {
                        "node_at_end_a": instance.get("instance_name") if node_counter == 0 else origin_node,
                        "node_at_end_b": origin_node if node_counter == 0 else instance.get("instance_name"),
                        "length": str(random.randint(6, 18)),
                        "angle": str(0 if node_counter == 0 else random.randint(0, 359)),
                        "diameter": "0.1"
                    })
                    node_counter += 1

        #else, if there are only two nodes already defined by the instances list (two connectors)
        elif len(nodes_from_instances_list) == 2:
            #make one segment
            segment_id = "segment"

            #that has two ends of the two nodes in the instances list
            segment_ends = []
            for instance in instances_list.read_instance_rows():
                if instance.get("item_type") == "Node":
                    segment_ends.append(instance.get("instance_name"))

            add_segment(segment_id, {
                "node_at_end_a": segment_ends[0],
                "node_at_end_b": segment_ends[1],
                "length": str(random.randint(6, 18)),
                "angle": str(0 if node_counter == 0 else random.randint(0, 359)),
                "diameter": "0.1"
            })

        else:
            raise ValueError("Fewer than two nodes defined, cannot build segments.")
    
    # --- Case 2: Some nodes exist in the formboard definition tsv but not all of them---
    else:
        nodes_from_instances_list_not_in_formboard_def = nodes_from_instances_list - nodes_from_formboard_definition

        if nodes_from_instances_list_not_in_formboard_def:
            if len(nodes_from_instances_list) > 2:
                addon_node = ""
                for instance in instances_list.read_instance_rows():
                    if instance.get("item_type") == "Node" and instance.get("parent_instance") == "":
                        addon_node = instance.get("instance_name")
                        break
                if not addon_node:
                    for instance in instances_list.read_instance_rows():
                        if instance.get("item_type") == "Node":
                            addon_node = instance.get("instance_name")
                            break

                for missing_node in nodes_from_instances_list_not_in_formboard_def:
                    instances_list.add_unless_exists(missing_node,{
                        "instance_name": missing_node,
                        "mpn": "N/A",
                        "item_type": "Node",
                        "location_is_node_or_segment": "Node"
                    })

                    segment_id = f"{missing_node}_leg"

                    whatever_node_to_attach_new_leg_to = ""
                    for instance in instances_list.read_instance_rows():
                        if instance.get("item_type") == "Node":
                            whatever_node_to_attach_new_leg_to = instance.get("instance_name")
                            continue
    
    for segment in read_segment_rows():
        instances_list.add_unless_exists(segment.get('segment_id'),{
            "mpn": "N/A",
            'item_type': 'Segment',
            'location_is_node_or_segment': "Segment",
            'length': segment.get('length'),
            'diameter': segment.get('diameter'),
            'node_at_end_a': segment.get('node_at_end_a'),
            'node_at_end_b': segment.get('node_at_end_b'),
            'absolute_rotation': segment.get('angle')
        })
    
    for node in nodes_from_formboard_definition:
        instances_list.add_unless_exists(node,{
            "mpn": "N/A",
            'item_type': 'Node',
            'location_is_node_or_segment': "Node",
        })

    # === Detect loops (from instances list) ===
    # Build adjacency from segments in instances list
    adjacency = defaultdict(list)
    for instance in instances_list.read_instance_rows():
        if instance.get("item_type") == "Segment":
            node_a = instance.get("node_at_end_a")
            node_b = instance.get("node_at_end_b")
            if node_a and node_b:
                adjacency[node_a].append(node_b)
                adjacency[node_b].append(node_a)

    # DFS to detect cycles
    visited = set()

    def dfs(node, parent):
        visited.add(node)
        for neighbor in adjacency[node]:
            if neighbor not in visited:
                if dfs(neighbor, node):
                    return True
            elif neighbor != parent:
                return True
        return False

    for node in adjacency:
        if node not in visited:
            if dfs(node, None):
                raise Exception("Loop detected in formboard graph. Would be cool, but Harnice doesn't support that yet.")

def generate_node_coordinates():
    # === Step 1: Read formboard graph definition ===
    try:
        with open(fileio.path("formboard graph definition"), "r") as file:
            segment_data = json.load(file)
    except FileNotFoundError:
        print(f"File not found: {fileio.name('formboard graph definition')}")
        return
    except json.JSONDecodeError:
        print(f"Invalid JSON in file: {fileio.name('formboard graph definition')}")
        return

    # === Step 2: Read instances list ===
    instances = instances_list.read_instance_rows()
    instance_lookup = {inst.get('instance_name', ''): inst for inst in instances}

    # === Step 3: Set origin node ===
    origin_node = ''
    for segment in segment_data.values():
        origin_node = segment.get("segment_end_a")
        break

    if not origin_node:
        print("No node found to initialize coordinates.")
        return

    print(f"-Origin node: '{origin_node}'")

    # === Step 4: Build graph structure ===
    graph = {}
    for segment in segment_data.values():
        a = segment.get("segment_end_a")
        b = segment.get("segment_end_b")
        if a and b:
            graph.setdefault(a, []).append((b, segment))
            graph.setdefault(b, []).append((a, segment))

    # === Step 5: Propagate node coordinates ===
    node_coordinates = {origin_node: (0.0, 0.0)}
    queue = deque([origin_node])

    while queue:
        current = queue.popleft()
        current_x, current_y = node_coordinates[current]

        for neighbor, segment in graph.get(current, []):
            if neighbor in node_coordinates:
                continue

            radians = math.radians(segment.get("angle"))
            length = segment.get("length", 0)
            dx = length * math.cos(radians)
            dy = length * math.sin(radians)

            new_x = round(current_x + dx, 2)
            new_y = round(current_y + dy, 2)
            node_coordinates[neighbor] = (new_x, new_y)
            queue.append(neighbor)

    # === Step 6: Update instances list with node coordinates ===
    for node_name, (x, y) in node_coordinates.items():
        instance = instance_lookup.get(node_name)
        if instance:
            instance['translate_x'] = str(x)
            instance['translate_y'] = str(y)

    # === Step 7: Prepare SVG visualization ===
    output_file_path = fileio.path("formboard graph definition svg")

    padding = 50
    radius = 5
    font_size = 12
    scale = 96  # 96 pixels per inch

    # Collect node coordinates for SVG
    node_coordinates_svg = {
        inst_name: (float(inst.get('translate_x', '')), float(inst.get('translate_y', '')))
        for inst_name, inst in instance_lookup.items()
        if inst.get('item_type') == 'Node' and inst.get('translate_x') and inst.get('translate_y')
    }

    if not node_coordinates_svg:
        print("No valid node coordinates found for SVG.")
        return

    all_x = [coord[0] * scale for coord in node_coordinates_svg.values()]
    all_y = [coord[1] * scale for coord in node_coordinates_svg.values()]
    min_x, max_x = min(all_x), max(all_x)
    min_y, max_y = min(all_y), max(all_y)
    width = max_x - min_x + 2 * padding
    height = max_y - min_y + 2 * padding

    def map_coordinates(x, y):
        return x * scale - min_x + padding, height - (y * scale - min_y + padding)

    svg_elements = []
    segment_midpoints = {}

    # Draw segments
    for segment_id, segment in segment_data.items():
        end_a_name = segment.get('segment_end_a', '')
        end_b_name = segment.get('segment_end_b', '')

        coord_a = node_coordinates_svg.get(end_a_name)
        coord_b = node_coordinates_svg.get(end_b_name)

        if coord_a and coord_b:
            start_x, start_y = map_coordinates(*coord_a)
            end_x, end_y = map_coordinates(*coord_b)

            # Midpoint in SVG units
            mid_x_svg = (start_x + end_x) / 2
            mid_y_svg = (start_y + end_y) / 2

            # Convert midpoint back to logical inches
            mid_x_logical = (mid_x_svg + min_x - padding) / scale
            mid_y_logical = (height - mid_y_svg + min_y - padding) / scale

            segment_midpoints[segment_id] = (round(mid_x_logical, 2), round(mid_y_logical, 2))

            svg_elements.append(
                f'<line x1="{start_x}" y1="{start_y}" x2="{end_x}" y2="{end_y}" '
                f'stroke="black" stroke-width="2" />'
            )
            svg_elements.append(
                f'<text x="{mid_x_svg}" y="{mid_y_svg}" font-size="{font_size}" '
                f'text-anchor="middle" fill="blue">{segment_id}</text>'
            )

    # Draw nodes
    for node_name, (x_logical, y_logical) in node_coordinates_svg.items():
        x, y = map_coordinates(x_logical, y_logical)
        label = node_name.removesuffix(".node")
        svg_elements.append(f'<circle cx="{x}" cy="{y}" r="{radius}" fill="red" />')
        svg_elements.append(
            f'<text x="{x}" y="{y - 10}" font-size="{font_size}" '
            f'text-anchor="middle" fill="black">{label}</text>'
        )

    # Write SVG file
    svg_content = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">'
        + "".join(svg_elements)
        + "</svg>"
    )
    with open(output_file_path, "w") as output_file:
        output_file.write(svg_content)

    # === Step 8: Write all modified instances back ===
    instances_list.write_instance_rows(instances)

def map_instance_to_segments(instance_name):
    # Ensure you're trying to map an instance that is segment-based.
    if not instances_list.attribute_of(instance_name, "location_is_node_or_segment") == "Segment":
        raise ValueError(f"You're trying to map a non segment-based instance {instance_name} across segments.")

    # Find terminal nodes from the ports
    prev_instance, next_instance = instances_list.instance_names_of_adjacent_ports(instance_name)
    node_of_prev_instance = instances_list.recursive_parent_search(prev_instance, "parent_instance", "item_type", "Node")
    node_of_next_instance = instances_list.recursive_parent_search(next_instance, "parent_instance", "item_type", "Node")

    # Build graph of segments
    segments = [
        inst for inst in instances_list.read_instance_rows()
        if inst.get("item_type") == "Segment"
    ]

    graph = {}
    segment_lookup = {}  # frozenset({A, B}) -> instance_name

    for seg in segments:
        a = seg.get("node_at_end_a")
        b = seg.get("node_at_end_b")
        seg_name = seg.get("instance_name")
        if not a or not b:
            continue
        graph.setdefault(a, set()).add(b)
        graph.setdefault(b, set()).add(a)
        segment_lookup[frozenset([a, b])] = seg_name

    # BFS to find a node path
    from collections import deque
    queue = deque([(node_of_prev_instance, [node_of_prev_instance])])
    visited = set()

    while queue:
        current, path = queue.popleft()
        if current in visited:
            continue
        visited.add(current)

        if current == node_of_next_instance:
            # Convert node path to segment names
            segment_path = []
            for i in range(len(path) - 1):
                a, b = path[i], path[i + 1]
                seg = segment_lookup.get(frozenset([a, b]))
                if seg:
                    segment_path.append(seg)
            break
        for neighbor in graph.get(current, []):
            if neighbor not in visited:
                queue.append((neighbor, path + [neighbor]))
    else:
        raise ValueError(f"No segment path found between {node_of_prev_instance} and {node_of_next_instance}")

    # Add a new instance for each connected segment
    for seg_name in segment_path:
        instances_list.add_unless_exists(f"{instance_name}.{seg_name}", {
            "item_type": "Hardware segment",
            "parent_instance": instance_name,
            "parent_csys": seg_name,
            "mpn": "N/A",
            "location_is_node_or_segment": "Segment",
            "length": instances_list.attribute_of(seg_name, 'length')
        })

def update_parent_csys():
    instances = instances_list.read_instance_rows()
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

    instances_list.write_instance_rows(instances)

def update_component_translate():
    instances = instances_list.read_instance_rows()
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

    instances_list.write_instance_rows(instances)
