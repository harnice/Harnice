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

    instances_list.add_nodes()
    #generate_node_coordinates()
    #visualize_formboard_graph()
    #map_connections_to_graph()

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
                "segment_end_a": connectors[0],
                "segment_end_b": connectors[1],
                "length": None,
                "angle": None,
                "diameter": 0.5
            }
    
    if more_than_two_connectors == True:
        for connector in connectors:
            segment_name = f"{base_segment_name}{segment_counter}"
            data[segment_name] = {
                "segment_end_a": "node1",
                "segment_end_b": connector,
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
        print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: File not found: {fileio.name("formboard graph definition")}")
        return
    except json.JSONDecodeError:
        print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Invalid JSON in file: {fileio.name("formboard graph definition")}")
        return

    # Initialize node coordinates
    node_coordinates = {"node1": (0, 0)}  # Assuming "node1" is the origin (0, 0)

    # To/from segment data
    segment_to_from_data = []
    
    # Track angles connected to each node
    node_angles = {node: [] for node in node_coordinates.keys()}


    # Calculate coordinates for each node
    for segment_name, segment in segment_data.items():
        segment_diameter = segment["diameter"]
        start_node = segment["segment_end_a"]
        end_node = segment["segment_end_b"]
        length = segment.get("length")
        angle = segment.get("angle")

        if start_node not in node_coordinates:
            print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Start node {start_node} is missing coordinates. Skipping segment.")
            continue

        if length is None or angle is None:
            print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Segment missing length or angle. Skipping segment.")
            continue

        # Calculate the coordinates of the end node
        start_x, start_y = node_coordinates[start_node]
        end_x = start_x + length * math.cos(math.radians(angle))
        end_y = start_y + length * math.sin(math.radians(angle))
        node_coordinates[end_node] = (round(end_x, 2), round(end_y, 2))

        # Calculate center coordinates
        center_x = (start_x + end_x) / 2
        center_y = (start_y + end_y) / 2
        center_coordinates = (round(center_x, 2), round(center_y, 2))
                
        # Track angles for the start and end nodes
        if start_node not in node_angles:
            node_angles[start_node] = []
        if end_node not in node_angles:
            node_angles[end_node] = []
        node_angles[start_node].append(angle)
        node_angles[end_node].append(angle)

        # Add "to", "from", and "center" data for the segment
        segment_to_from_data.append({
            "segment name": segment_name,
            "diameter": segment_diameter,
            "from": {"node": start_node, "coordinates": (round(start_x, 2), round(start_y, 2))},
            "to": {"node": end_node, "coordinates": (round(end_x, 2), round(end_y, 2))},
            "center": {"coordinates": center_coordinates}
        })


    # Calculate average angles for each node
    node_coordinates_with_angles = {}
    for node, (x, y) in node_coordinates.items():
        connected_angles = node_angles.get(node, [])
        avg_angle = round(sum(connected_angles) / len(connected_angles), 2) if connected_angles else None
        node_coordinates_with_angles[node] = {
            "coords": (x, y),
            "angle": avg_angle
        }

    # Write the node coordinates (with average angles) as-is to the inches file
    with open(fileio.path("formboard node locations inches"), "w") as file:
        json.dump(node_coordinates_with_angles, file, indent=4)

    # Write the node coordinates as-is to the inches file
    #with open(fileio.path("formboard node locations inches"), "w") as file:
        #json.dump(node_coordinates, file, indent=4)

    # Create the pixel coordinates by multiplying each value by 96
    node_coordinates_px = {
        node: (round(x * 96, 2), round(y * 96, 2)) 
        for node, (x, y) in node_coordinates.items()
    }

    # Write the pixel coordinates to the px file
    with open(fileio.path("formboard node locations px"), "w") as file:
        json.dump(node_coordinates_px, file, indent=4)

    # Write the segment "to", "from", and "center" data to the file
    with open(fileio.path("formboard segment to from center"), "w") as file:
        json.dump(segment_to_from_data, file, indent=4)

    print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Node coordinates written to {fileio.path("formboard node locations inches")}")
    print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Node coordinates written to {fileio.path("formboard node locations px")}")
    print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Segment to/from/center data written to {fileio.path("formboard segment to from center")}")

def visualize_formboard_graph():
    node_file_path = fileio.path("formboard node locations px")
    output_file_path = fileio.path("formboard graph definition svg")

    # Read the segment and node data
    try:
        with open(fileio.path("formboard graph definition"), "r") as segment_file:
            segment_data = json.load(segment_file)
        with open(node_file_path, "r") as node_file:
            node_coordinates = json.load(node_file)
    except FileNotFoundError as e:
        print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: File not found: {e.utility.filename}")
        return
    except json.JSONDecodeError:
        print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Invalid JSON in one of the input files.")
        return

    # SVG setup
    svg_elements = []
    padding = 50  # Add padding to the SVG canvas
    radius = 5  # Radius for the nodes
    font_size = 12  # Font size for labels

    # Determine SVG canvas size
    all_x = [coord[0] for coord in node_coordinates.values()]
    all_y = [coord[1] for coord in node_coordinates.values()]
    min_x, max_x = min(all_x), max(all_x)
    min_y, max_y = min(all_y), max(all_y)
    width = max_x - min_x + 2 * padding
    height = max_y - min_y + 2 * padding

    # Map coordinates to SVG canvas
    def map_coordinates(x, y):
        return x - min_x + padding, height - (y - min_y + padding)

    # Draw segments
    for segment_id, segment in segment_data.items():
        start_node = segment["segment_end_a"]
        end_node = segment["segment_end_b"]
        if start_node in node_coordinates and end_node in node_coordinates:
            start_x, start_y = map_coordinates(*node_coordinates[start_node])
            end_x, end_y = map_coordinates(*node_coordinates[end_node])
            svg_elements.append(
                f'<line x1="{start_x}" y1="{start_y}" x2="{end_x}" y2="{end_y}" '
                f'stroke="black" stroke-width="2" />'
            )
            # Add label for the segment using the segment ID
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
        # Add label for the node
        svg_elements.append(
            f'<text x="{x}" y="{y - 10}" font-size="{font_size}" '
            f'text-anchor="middle" fill="black">{node}</text>'
        )

    # Assemble the SVG
    svg_content = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">'
        + "".join(svg_elements)
        + "</svg>"
    )

    # Write to file
    with open(output_file_path, "w") as output_file:
        output_file.write(svg_content)

    print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: SVG graph visualization written to {output_file_path}")

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

if __name__ == "__main__":
    formboard_processor()