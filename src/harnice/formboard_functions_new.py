import json
import os
import random
import math
from collections import deque
import instances_list
import fileio
import csv

def validate_nodes():
    instances = instances_list.read_instance_rows()
    instance_lookup = {instance.get('instance_name'): instance for instance in instances if instance.get('instance_name')}
    new_instance_rows = []  # <--- Track new nodes to add

    # Collect connector names directly
    num_connectors = 0
    for instance in instances:
        if instance.get('item_type') == 'Connector':
            num_connectors += 1

    print(f"num_connectors: {num_connectors}")

    # Try to load existing formboard graph
    try:
        with open(fileio.path("formboard graph definition"), 'r') as f:
            formboard_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        formboard_data = {}

    segment_ids = list(formboard_data.keys())
    print(f"segment_ids: {segment_ids}")

    # Collect all relevant node names
    all_node_names = [
        instance.get('instance_name')
        for instance in instances
        if instance.get('item_type') == 'Node'
    ]
    print(f"all_node_names: {all_node_names}")

    # Extract all nodes already involved in segments
    nodes_in_segments = set()
    for segment in formboard_data.values():
        nodes_in_segments.add(segment.get('segment_end_a', ''))
        nodes_in_segments.add(segment.get('segment_end_b', ''))
    nodes_in_segments.discard('')  # Clean up blanks
    print(f"nodes_in_segments: {nodes_in_segments}")

    # --- Case 1: No segments exist yet ---
    if not segment_ids:
        if num_connectors > 2:
            origin_node = "node1"
            node_counter = 0
            for instance in instances:
                if instance.get("item_type") == "Node":
                    segment_name = instance.get("parent_instance") + "_leg"
                    formboard_data[segment_name] = {
                        "segment_end_a": origin_node,
                        "segment_end_b": instance.get("instance_name"),
                        "length": random.randint(6, 18),
                        "angle": 0 if node_counter == 0 else random.randint(0, 359),
                        "diameter": 0.1
                    }
                    node_counter += 1
        elif num_connectors == 2:
            # Two connectors: direct connection (connect their .node entries)
            segment_name = "segment"
            segment_end = []

            for instance in instances:
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
            for instance in instances:
                if instance.get('item_type') == "Node" and instance.get('parent_instance') == "":
                    addon_new_seg_from_node = instance.get('instance_name')
                    break

            if addon_new_seg_from_node == "":
                for instance in instances:
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
    origin_node = None
    for instance in instances:
        if instance.get('item_type') == "Node":
            origin_node = instance.get('instance_name')
            break

    if not origin_node:
        print("No node found to initialize coordinates.")
        return

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

    print("SVG graph visualization written.")

    # === Step 8: Update instances list with segment midpoints ===
    for segment_name, (mid_x, mid_y) in segment_midpoints.items():
        instance = instance_lookup.get(segment_name)
        if instance:
            instance['translate_x'] = str(mid_x)
            instance['translate_y'] = str(mid_y)

    # === Step 9: Write all modified instances back ===
    instances_list.write_instance_rows(instances)
    print("Node and segment coordinates updated in instances list.")


