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

import csv
from harnice import fileio

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

def add_segment(segment_id, segment_data):
    """
    Adds a new segment to the formboard graph definition TSV.

    Args:
        segment_id (str): Unique segment identifier.
        segment_data (dict): Dictionary of segment attributes. May include "segment_id".

    Raises:
        ValueError: If segment_id is missing, already exists, or conflicts with segment_data["segment_id"].
    """
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
    # make a formboard definition file from scratch if it doesn't exist
    if not os.path.exists(fileio.name("formboard graph definition")):
        with open(fileio.name("formboard graph definition"), 'w') as f:
            pass  # Creates an empty file

    instances = instances_list.read_instance_rows()
    new_instance_rows = []  # <--- Track new nodes to add

    # Collect connector names directly
    num_connectors = 0
    for instance in instances:
        if instance.get('item_type') == 'Connector':
            num_connectors += 1

    # Try to load existing formboard graph
    try:
        with open(fileio.path("formboard graph definition"), 'r') as f:
            formboard_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        formboard_data = {}

    segment_ids = list(formboard_data.keys())

    # Collect all relevant node names
    all_node_names = [
        instance.get('instance_name')
        for instance in instances
        if instance.get('item_type') == 'Node'
    ]

    # Extract all nodes already involved in segments
    nodes_in_segments = set()
    for segment in formboard_data.values():
        nodes_in_segments.add(segment.get('segment_end_a', ''))
        nodes_in_segments.add(segment.get('segment_end_b', ''))
    nodes_in_segments.discard('')  # Clean up blanks

    # --- Case 1: No segments exist yet ---
    if not segment_ids:
        if num_connectors > 2:
            origin_node = "node1"
            node_counter = 0
            for instance in instances_list.read_instance_rows():
                if instance.get("item_type") == "Node":
                    segment_name = instance.get("parent_instance") + "_leg"
                    formboard_data[segment_name] = {
                        "segment_end_a": instance.get("instance_name") if node_counter == 0 else origin_node,
                        "segment_end_b": origin_node if node_counter == 0 else instance.get("instance_name"),
                        "length": random.randint(6, 18),
                        "angle": 0 if node_counter == 0 else random.randint(0, 359),
                        "diameter": 0.1
                    }
                    node_counter += 1
        elif num_connectors == 2:
            # Two connectors: direct connection (connect their .node entries)
            segment_name = "segment"
            segment_end = []

            for instance in instances_list.read_instance_rows():
                if instance.get("item_type") == "Node":
                    segment_end.append(instance.get("instance_name"))

            if len(segment_end) != 2:
                raise ValueError("Error: Expected exactly two nodes to connect, but found different number.")

            formboard_data[segment_name] = {
                "segment_end_a": segment_end[0],
                "segment_end_b": segment_end[1],
                "length": random.randint(6, 18),
                "angle": 0,
                "diameter": 0.1
            }
        else:
            raise ValueError("Error: Fewer than two connectors defined, cannot build segments.")

    # --- Case 2: Segments already exist ---
    else:
        missing_nodes = set(all_node_names) - nodes_in_segments

        if not missing_nodes:
            # Success — all nodes are represented
            return

        if num_connectors > 2:
            addon_new_seg_from_node = ""
            for instance in instances_list.read_instance_rows():
                if instance.get('item_type') == "Node" and instance.get('parent_instance') == "":
                    addon_new_seg_from_node = instance.get('instance_name')
                    break

            if addon_new_seg_from_node == "":
                for instance in instances_list.read_instance_rows():
                    if instance.get('item_type') == "Node":
                        addon_new_seg_from_node = instance.get('instance_name')
                        break

            for node_counter, missing_node in enumerate(missing_nodes):
                segment_name = f"{missing_node}_leg"
                if segment_name in formboard_data:
                    continue

                formboard_data[segment_name] = {
                    "segment_end_a": addon_new_seg_from_node,
                    "segment_end_b": missing_node,
                    "length": random.randint(6, 18),
                    "angle": random.randint(0, 359),
                    "diameter": 0.1
                }

        else:
            raise ValueError("Unexpected condition: Missing nodes but <= 2 connectors. Should have been caught earlier.")

    # Save updated formboard graph
    with open(fileio.path("formboard graph definition"), 'w') as f:
        json.dump(formboard_data, f, indent=2)

    # Append new rows to instances list if any
    if new_instance_rows:
        instances_list.append_instance_rows(new_instance_rows)

    instances_list.add_nodes_from_formboard()
    instances_list.add_segments_from_formboard()
    formboard.detect_loops()
    formboard.detect_dead_segments()

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

def map_cables_to_segments():
    from collections import defaultdict, deque

    instances = instances_list.read_instance_rows()

    wirelist = []
    with open(fileio.path("wirelist no formats"), 'r', newline='') as file:
        reader = csv.DictReader(file, delimiter='\t')
        for row in reader:
            wirelist.append({k: v for k, v in row.items()})

    try:
        with open(fileio.path("formboard graph definition"), 'r') as file:
            formboard_graph_definition = json.load(file)
    except FileNotFoundError:
        print(f"Graph definition file not found: {fileio.name('formboard graph definition')}")
        return

    graph = defaultdict(set)
    segment_map = {}
    for segment_id, details in formboard_graph_definition.items():
        node_a = details.get('segment_end_a', '')
        node_b = details.get('segment_end_b', '')
        length = details.get('length', 0)

        if not node_a or not node_b:
            continue

        graph[node_a].add(node_b)
        graph[node_b].add(node_a)

        segment_map[frozenset([node_a, node_b])] = {
            'segment': segment_id,
            'length': length
        }

    def find_path_with_segments(source_node, destination_node):
        if source_node not in graph or destination_node not in graph:
            return [], 0
        queue = deque([(source_node, [], 0)])
        visited = set()
        while queue:
            current, segment_path, total_length = queue.popleft()
            if current == destination_node:
                return segment_path, total_length
            if current in visited:
                continue
            visited.add(current)
            for neighbor in graph[current]:
                if neighbor not in visited:
                    seg_info = segment_map.get(frozenset([current, neighbor]), {})
                    seg_id = seg_info.get('segment')
                    seg_length = seg_info.get('length', 0)
                    queue.append((neighbor, segment_path + [seg_id], total_length + seg_length))
        return [], 0

    connections_to_graph = {}

    for instance in instances:
        if instance.get('item_type') != 'Cable':
            continue

        cable_name = instance.get('instance_name')
        if not cable_name:
            continue

        matching_rows = [row for row in wirelist if row.get('Wire', '') == cable_name]

        if not matching_rows:
            continue

        total_segments = []
        total_cable_length = 0

        for row in matching_rows:
            source_connector = row.get('Source', '').strip()
            destination_connector = row.get('Destination', '').strip()

            if not source_connector or not destination_connector:
                continue

            source_node = f"{source_connector}.node"
            destination_node = f"{destination_connector}.node"

            segment_path, path_length = find_path_with_segments(source_node, destination_node)

            if not segment_path:
                raise ValueError(
                    f"Path not found between {source_node} and {destination_node} for cable '{cable_name}'."
                )

            total_segments.extend(segment_path)
            total_cable_length += path_length

        if not total_segments:
            continue

        connections_to_graph[cable_name] = {
            "segments": total_segments,
            "total_length": total_cable_length
        }

    output_path = fileio.path("connections to graph")
    with open(output_path, 'w') as file:
        json.dump(connections_to_graph, file, indent=4)

    instances_list.write_instance_rows(instances)
    print("-All cables have valid paths from start connector to end connector via segments.")

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
