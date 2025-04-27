import os
import json
import csv
import random
import math
import instances_list
import yaml
from os.path import basename
from inspect import currentframe
import fileio
from collections import defaultdict

def formboard_processor():
    num_connectors = get_num_connectors()
    precheck_result = generate_segments_precheck()
    """
                segment file       length and angle data
            2:   false              false
            1:   TRUE               false
            -1:  TRUE               partial
            0:   TRUE               TRUE
    """
        #2: Segment file does not exist yet. Generating a basic wheel-spoke net. Modify {fileio.name("formboard graph definition")} as needed.
        #1: Segments already exist, but no length or angle data exists yet
        #-1: Only some length and angle data exits. Complete this file before rerunning. Aborting formboard generation process.
        #0: Length and angle data already exist for each segment. Preserving this data and exiting.
    
    if(precheck_result) == 2:
        if num_connectors < 2:
            raise ValueError("At least two connectors are required to generate segments.")

        if num_connectors == 2:
            generate_segments(False)
            add_random_lengths_angles()

        if num_connectors > 2:
            generate_segments(True)
            add_random_lengths_angles()

    if(precheck_result) == 1:
        add_random_lengths_angles()

    if(precheck_result) == -1:
        raise ValueError(f"Only some length and angle data exits in file {fileio.name("formboard graph definition")}. Complete this file before rerunning.")

def generate_segments_precheck():
    """Generates the graph definition with lengths and angles set to null."""
    # Step 2: Check if the file exists
    if os.path.exists(fileio.path("formboard graph definition")):
        # Load the existing file
        with open(fileio.path("formboard graph definition"), "r") as json_file:
            try:
                data = json.load(json_file)
            except json.JSONDecodeError:
                print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Error: Existing JSON file is invalid. Recreating it.")
                data = {}

        # Check "length" and "angle" values
        length_has_null = field_contains_null(fileio.path("formboard graph definition"), "length")
        length_has_numbers = field_contains_numbers(fileio.path("formboard graph definition"), "length")
        angle_has_null = field_contains_null(fileio.path("formboard graph definition"), "angle")
        angle_has_numbers = field_contains_numbers(fileio.path("formboard graph definition"), "angle")

        all_has_null = (
            not length_has_numbers
            and not angle_has_numbers
        )

        all_has_numbers = (
            not length_has_null
            and not angle_has_null
        )

        mixed_null_and_numbers = (
            not all_has_numbers
            and not all_has_null
        )

        if(all_has_null == True):
            #Segments already exist, but no length or angle data exists yet.
            return 1

        if(all_has_numbers == True):
            #Length and angle data already exist for each segment. Preserving this data.
            return 0

        if(mixed_null_and_numbers == True):
            #Only some length and angle data exits. Complete this file before rerunning. Aborting formboard generation process.
            return -1

    #else: (all other options have returned before this point)
    #Segment file does not exist yet. Generating a basic wheel-spoke net. Modify {fileio.name("formboard graph definition")} as needed.
    return 2

def generate_segments(more_than_two_connectors):
    # Read connectors from the instances list
    connectors = []
    with open(fileio.path("instances list"), mode='r') as tsv_file:
        reader = csv.DictReader(tsv_file, delimiter='\t')
        for row in reader:
            if row["item_type"] == "Connector":
                connectors.append(row["instance_name"])

    base_segment_name = "segment"
    segment_counter = 1
    data = {}

    # Create segments with specified fields

    if more_than_two_connectors == False:
        segment_name = f"{base_segment_name}{segment_counter}"
        data[segment_name] = {
                "segment_end_a": connectors[0] + ".node",
                "segment_end_b": connectors[1] + ".node",
                "length": None,
                "angle": None,
                "diameter": 0.5
            }
    
    if more_than_two_connectors == True:
        for connector in connectors:
            segment_name = f"{base_segment_name}{segment_counter}"
            data[segment_name] = {
                "segment_end_a": "node1",
                "segment_end_b": connector + ".node",
                "length": None,
                "angle": None,
                "diameter": 0.5
            }
            segment_counter += 1

    # Save the graph definition to JSON
    with open(fileio.path("formboard graph definition"), "w") as json_file:
        json.dump(data, json_file, indent=4)
        print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Graph definition saved to {fileio.path("formboard graph definition")}")

    return True

def add_random_lengths_angles():
    # Read the existing JSON data
    try:
        with open(fileio.path("formboard graph definition"), "r") as file:
            data = json.load(file)
    except FileNotFoundError:
        print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: File not found: {fileio.name("formboard graph definition")}")
        return
    except json.JSONDecodeError:
        print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Invalid JSON in file: {fileio.name("formboard graph definition")}")
        return

    # Update the "length" and "angle" fields
    segment_counter = 0
    for segment in data.values():
        if segment_counter == 0:
            #the first segment is horizontal
            segment["angle"] = 0
        else:
            #all other segments are random
            segment["angle"] = random.randint(0, 359)

        segment["length"] = random.randint(6, 18)
        segment_counter += 1

    # Write the updated data back to the JSON file
    with open(fileio.path("formboard graph definition"), "w") as file:
        json.dump(data, file, indent=4)

    print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Added random lengths and angles to {fileio.name("formboard graph definition")}")

def generate_node_coordinates():
    # Read the segment data
    try:
        with open(fileio.path("formboard graph definition"), "r") as file:
            segment_data = json.load(file)
    except FileNotFoundError:
        print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: File not found: {fileio.name('formboard graph definition')}")
        return
    except json.JSONDecodeError:
        print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Invalid JSON in file: {fileio.name('formboard graph definition')}")
        return

    # Read the instances list
    with open(fileio.path("instances list"), newline='') as tsv_file:
        reader = csv.DictReader(tsv_file, delimiter='\t')
        rows = list(reader)
        fieldnames = reader.fieldnames or []

    for i, row in enumerate(rows):
        if None in row:
            print(f"Row {i} has extra columns: {row[None]}")
            del row[None]

    for field in ['translate_x', 'translate_y', 'instance_name']:
        if field not in fieldnames:
            fieldnames.append(field)

    row_lookup = {row['instance_name']: row for row in rows if 'instance_name' in row}

    # Set origin as first connector
    origin_node = None
    for row in rows:
        if row.get("item_type") == "Connector":
            origin_node = row.get("instance_name")
            break

    if origin_node is None:
        print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: No connector found to initialize coordinates.")
        return

    # Build graph structure to traverse
    graph = {}
    for name, segment in segment_data.items():
        a = segment["segment_end_a"]
        b = segment["segment_end_b"]
        graph.setdefault(a, []).append((b, segment))
        graph.setdefault(b, []).append((a, segment))  # bidirectional for traversal

    # Coordinate assignment (propagation from origin)
    visited = set()
    node_coordinates = {origin_node: (0, 0)}
    queue = [origin_node]

    while queue:
        current = queue.pop(0)
        visited.add(current)
        current_x, current_y = node_coordinates[current]

        for neighbor, segment in graph.get(current, []):
            if neighbor in node_coordinates:
                continue  # already assigned

            if segment["segment_end_a"] == current:
                direction = 1
                angle = segment["angle"]
            elif segment["segment_end_b"] == current:
                direction = -1
                angle = (segment["angle"] + 180) % 360
            else:
                continue  # shouldn't happen

            length = segment["length"]
            dx = length * math.cos(math.radians(angle)) * direction
            dy = length * math.sin(math.radians(angle)) * direction

            new_x = round(current_x + dx, 2)
            new_y = round(current_y + dy, 2)
            node_coordinates[neighbor] = (new_x, new_y)
            queue.append(neighbor)

    # Write all node coordinates back to *.node rows
    for node, (x, y) in node_coordinates.items():
        target_name = f"{node}.node"
        if target_name in row_lookup:
            row_lookup[target_name]['translate_x'] = f"{x}"
            row_lookup[target_name]['translate_y'] = f"{y}"

    # Write to file
    with open(fileio.path("instances list"), mode='w', newline='') as tsv_file:
        writer = csv.DictWriter(tsv_file, fieldnames=fieldnames, delimiter='\t', extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)

    print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: All node coordinates written to instances list.")

def visualize_formboard_graph():
    output_file_path = fileio.path("formboard graph definition svg")

    # Read the segment data
    try:
        with open(fileio.path("formboard graph definition"), "r") as segment_file:
            segment_data = json.load(segment_file)
    except FileNotFoundError as e:
        print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: File not found: {e.filename}")
        return
    except json.JSONDecodeError:
        print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Invalid JSON in formboard graph definition.")
        return

    # Read node coordinates from instances list (.node entries only)
    node_coordinates = {}
    try:
        with open(fileio.path("instances list"), newline='') as tsv_file:
            reader = csv.DictReader(tsv_file, delimiter='\t')
            for row in reader:
                name = row.get("instance_name", "")
                if not name.endswith(".node"):
                    continue
                try:
                    x = float(row.get("translate_x", ""))
                    y = float(row.get("translate_y", ""))
                    node_coordinates[name] = (x, y)
                except (ValueError, TypeError):
                    continue
    except FileNotFoundError as e:
        print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: File not found: {e.filename}")
        return

    if not node_coordinates:
        print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: No valid .node coordinates found.")
        return

    # SVG setup
    svg_elements = []
    padding = 50  # padding in pixels
    radius = 5
    font_size = 12
    scale = 96  # scale from inches to pixels

    all_x = [coord[0] * scale for coord in node_coordinates.values()]
    all_y = [coord[1] * scale for coord in node_coordinates.values()]
    min_x, max_x = min(all_x), max(all_x)
    min_y, max_y = min(all_y), max(all_y)
    width = max_x - min_x + 2 * padding
    height = max_y - min_y + 2 * padding

    def map_coordinates(x, y):
        return x * scale - min_x + padding, height - (y * scale - min_y + padding)

    # Draw segments
    for segment_id, segment in segment_data.items():
        start_node_key = f"{segment['segment_end_a']}.node"
        end_node_key = f"{segment['segment_end_b']}.node"
        if start_node_key in node_coordinates and end_node_key in node_coordinates:
            start_x, start_y = map_coordinates(*node_coordinates[start_node_key])
            end_x, end_y = map_coordinates(*node_coordinates[end_node_key])
            svg_elements.append(
                f'<line x1="{start_x}" y1="{start_y}" x2="{end_x}" y2="{end_y}" '
                f'stroke="black" stroke-width="2" />'
            )
            mid_x, mid_y = (start_x + end_x) / 2, (start_y + end_y) / 2
            svg_elements.append(
                f'<text x="{mid_x}" y="{mid_y}" font-size="{font_size}" '
                f'text-anchor="middle" fill="blue">{segment_id}</text>'
            )

    # Draw nodes
    for node, coord in node_coordinates.items():
        x, y = map_coordinates(*coord)
        svg_elements.append(
            f'<circle cx="{x}" cy="{y}" r="{radius}" fill="red" />'
        )
        svg_elements.append(
            f'<text x="{x}" y="{y - 10}" font-size="{font_size}" '
            f'text-anchor="middle" fill="black">{node}</text>'
        )

    svg_content = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">'
        + "".join(svg_elements)
        + "</svg>"
    )

    with open(output_file_path, "w") as output_file:
        output_file.write(svg_content)

    print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: SVG graph visualization written to {output_file_path}")

def get_num_connectors():
    connectors = []
    with open(fileio.path("instances list"), mode='r') as tsv_file:
        reader = csv.DictReader(tsv_file, delimiter='\t')
        for row in reader:
            if row["item_type"] == "Connector":
                connectors.append(row["instance_name"])
    return len(connectors)

def field_contains_null(file_path, field):
    """Checks if the specified field contains any null values in the JSON file."""
    try:
        with open(file_path, "r") as file:
            data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        print("from {basename(__file__)} > {currentframe().f_code.co_name}: Error: File not found or invalid JSON format.")
        return False

    for item in data.values():
        if item.get(field) is None:
            return True  # Found at least one null value
    return False

def field_contains_numbers(file_path, field):
    """Checks if the specified field contains any numerical values in the JSON file."""
    try:
        with open(file_path, "r") as file:
            data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        print("from {basename(__file__)} > {currentframe().f_code.co_name}: Error: File not found or invalid JSON format.")
        return False

    for item in data.values():
        if isinstance(item.get(field), (int, float)):
            return True  # Found at least one numerical value
    return False

def map_connections_to_graph():
    """Maps connections from a wirelist to a formboard graph, calculates total lengths, and outputs the result as a JSON file."""
    output_path = fileio.path("connections to graph")

    # Read the wirelist TSV file
    try:
        with open(fileio.path("wirelist no formats"), 'r') as file:
            reader = csv.DictReader(file, delimiter='\t')
            wirelist = [row for row in reader]
    except FileNotFoundError:
        raise FileNotFoundError(f"Wirelist file not found: {fileio.name("wirelist no formats")}")

    # Load the graph definition JSON
    try:
        with open(fileio.path("formboard graph definition"), 'r') as f:
            graph_definition = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Graph definition file not found: {fileio.name("formboard graph definition")}")

    # Parse the graph into adjacency lists and track segments
    graph = defaultdict(set)
    segment_map = {}  # Maps node pairs to their connecting segment
    for segment, details in graph_definition.items():
        node_a = details["segment_end_a"]
        node_b = details["segment_end_b"]
        length = details.get("length", 0)

        # Add nodes to adjacency list
        graph[node_a].add(node_b)
        graph[node_b].add(node_a)

        # Map the segment details to the node pair
        segment_map[frozenset([node_a, node_b])] = {
            "segment": segment,
            "length": length
        }

    # Function to find the path and segments from source to destination using BFS
    def find_path_with_segments(source, destination):
        if source not in graph or destination not in graph:
            return [], 0
        queue = [(source, [source], [], 0)]  # (current node, path of nodes, path of segments, total length)
        visited = set()
        while queue:
            current, node_path, segment_path, total_length = queue.pop(0)  # FIFO queue
            if current == destination:
                return segment_path, total_length
            if current in visited:
                continue
            visited.add(current)
            for neighbor in graph[current]:
                if neighbor not in visited:
                    segment_details = segment_map.get(frozenset([current, neighbor]), {})
                    segment = segment_details.get("segment")
                    length = segment_details.get("length", 0)
                    queue.append(
                        (neighbor, node_path + [neighbor], segment_path + [segment], total_length + length)
                    )
        return [], 0

    # Generate the connections-to-graph JSON
    connections_to_graph = {}
    for row in wirelist:
        wire = row['Wire']
        subwire = row['Subwire']
        source = row['Source']
        destination = row['Destination']
        segment_path, total_length = find_path_with_segments(source, destination)
        if not segment_path:
            print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Warning: No path found for {wire} - {subwire} from {source} to {destination}")
            continue
        if wire not in connections_to_graph:
            connections_to_graph[wire] = {"subconnections": {}, "wirelength": 0}
        connections_to_graph[wire]["subconnections"][subwire] = {
            "segments": segment_path,
            "total_length": total_length
        }
        # Update the wirelength as the maximum total_length among subconnections
        connections_to_graph[wire]["wirelength"] = max(connections_to_graph[wire]["wirelength"], total_length)

    # Save the output JSON
    with open(fileio.path("connections to graph"), 'w') as f:
        json.dump(connections_to_graph, f, indent=4)

    print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Wires mapped to segments at: {fileio.name("connections to graph")}")


if __name__ == "__main__":
    formboard_processor()