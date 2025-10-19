import os
import random
import math
import csv
from PIL import Image, ImageDraw, ImageFont
from collections import defaultdict, deque
from harnice import instances_list, fileio, circuit_instance

FORMBOARD_TSV_COLUMNS = [
    "segment_id",
    "node_at_end_a",
    "node_at_end_b",
    "length",
    "angle",
    "diameter",
]


def read_segment_rows():
    """
    Reads all rows from the formboard graph definition TSV.

    Returns:
        List[dict]: Each row as a dictionary with keys from FORMBOARD_TSV_COLUMNS.
    """
    with open(
        fileio.path("formboard graph definition"), newline="", encoding="utf-8"
    ) as f:
        return list(csv.DictReader(f, delimiter="\t"))


def write_segment_rows(rows):
    with open(
        fileio.path("formboard graph definition"), "w", newline="", encoding="utf-8"
    ) as f:
        writer = csv.DictWriter(
            f, fieldnames=FORMBOARD_TSV_COLUMNS, delimiter="\t", lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)
        f.write("\n")


def add_segment_to_formboard_def(segment_id, segment_data):
    if not segment_id:
        raise ValueError(
            "Argument 'segment_id' is blank and required to identify a unique segment"
        )

    segments = read_segment_rows()
    if any(row.get("segment_id") == segment_id for row in segments):
        return True

    # Ensure the segment_id is included in the data
    segment_data["segment_id"] = segment_id

    path = fileio.path("formboard graph definition")

    with open(path, "a+", encoding="utf-8") as f:
        f.seek(0, os.SEEK_END)
        if f.tell() > 0:
            f.seek(f.tell() - 1)
            if f.read(1) != "\n":
                f.write("\n")

        writer = csv.DictWriter(
            f,
            fieldnames=FORMBOARD_TSV_COLUMNS,
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writerow(
            {key: segment_data.get(key, "") for key in FORMBOARD_TSV_COLUMNS}
        )

    return False


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
    if not os.path.exists(fileio.path("formboard graph definition")):
        with open(
            fileio.path("formboard graph definition"), "w", newline="", encoding="utf-8"
        ) as f:
            writer = csv.DictWriter(f, delimiter="\t", fieldnames=FORMBOARD_TSV_COLUMNS)
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
        if len(nodes_from_instances_list) > 2:
            origin_node = "node1"
            node_counter = 0
            for instance in instances_list.read_instance_rows():
                if instance.get("item_type") == "Node":
                    segment_id = instance.get("instance_name") + "_leg"
                    add_segment_to_formboard_def(
                        segment_id,
                        {
                            "node_at_end_a": (
                                instance.get("instance_name")
                                if node_counter == 0
                                else origin_node
                            ),
                            "node_at_end_b": (
                                origin_node
                                if node_counter == 0
                                else instance.get("instance_name")
                            ),
                            "length": str(random.randint(6, 18)),
                            "angle": str(
                                0 if node_counter == 0 else random.randint(0, 359)
                            ),
                            "diameter": 0.1,
                        },
                    )
                    node_counter += 1

        elif len(nodes_from_instances_list) == 2:
            segment_id = "segment"
            segment_ends = []
            for instance in instances_list.read_instance_rows():
                if instance.get("item_type") == "Node":
                    segment_ends.append(instance.get("instance_name"))

            add_segment_to_formboard_def(
                segment_id,
                {
                    "segment_id": segment_id,
                    "node_at_end_a": segment_ends[0],
                    "node_at_end_b": segment_ends[1],
                    "length": str(random.randint(6, 18)),
                    "angle": str(0),
                    "diameter": 0.1,
                },
            )

        else:
            raise ValueError("Fewer than two nodes defined, cannot build segments.")

    # --- Case 2: Some nodes from instances list exist in the formboard definition but not all of them ---
    else:
        nodes_from_instances_list_not_in_formboard_def = (
            nodes_from_instances_list - nodes_from_formboard_definition
        )

        if nodes_from_instances_list_not_in_formboard_def:
            for missing_node in nodes_from_instances_list_not_in_formboard_def:
                segment_id = f"{missing_node}_leg"

                node_to_attach_new_leg_to = ""
                for instance in instances_list.read_instance_rows():
                    if (
                        instance.get("item_type") == "Node"
                        and instance.get("instance_name") != missing_node
                    ):
                        node_to_attach_new_leg_to = instance.get("instance_name")
                        break

                if not node_to_attach_new_leg_to:
                    raise ValueError(
                        f"No existing node found to connect {missing_node} to."
                    )

                add_segment_to_formboard_def(
                    segment_id,
                    {
                        "segment_id": segment_id,
                        "node_at_end_a": missing_node,
                        "node_at_end_b": node_to_attach_new_leg_to,
                        "length": str(random.randint(6, 18)),
                        "angle": str(random.randint(0, 359)),
                        "diameter": 0.1,
                    },
                )

    # === CLEANUP: remove obsolete one-leg nodes ===
    # These nodes represent old connectors that no longer exist in the harness definition.
    segments = read_segment_rows()
    node_occurrences = defaultdict(int)
    for seg in segments:
        node_occurrences[seg.get("node_at_end_a")] += 1
        node_occurrences[seg.get("node_at_end_b")] += 1

    # Find nodes that appear in exactly one segment and are not in the current instances list
    obsolete_nodes = [
        node
        for node, count in node_occurrences.items()
        if count == 1 and node not in nodes_from_instances_list
    ]

    if obsolete_nodes:
        cleaned_segments = []
        for seg in segments:
            if (
                seg.get("node_at_end_a") in obsolete_nodes
                or seg.get("node_at_end_b") in obsolete_nodes
            ):
                continue  # delete this segment
            cleaned_segments.append(seg)
        write_segment_rows(cleaned_segments)

    # === Sync formboard definition with instances list ===
    for segment in read_segment_rows():
        instances_list.new_instance(
            segment.get("segment_id"),
            {
                "item_type": "Segment",
                "location_is_node_or_segment": "Segment",
                "length": segment.get("length"),
                "diameter": segment.get("diameter"),
                "parent_csys_instance_name": segment.get("node_at_end_a"),
                "parent_csys_outputcsys_name": "origin",
                "node_at_end_a": segment.get("node_at_end_a"),
                "node_at_end_b": segment.get("node_at_end_b"),
                "absolute_rotation": segment.get("angle"),
            },
        )

    for node in nodes_from_formboard_definition:
        try:  # if this node already exists, that's ok we don't have to add it again
            instances_list.new_instance(
                node,
                {
                    "item_type": "Node",
                    "location_is_node_or_segment": "Node",
                    "parent_csys_instance_name": "origin",
                    "parent_csys_outputcsys_name": "origin",
                },
            )
        except ValueError:
            pass

    # === Detect loops ===
    adjacency = defaultdict(list)
    for instance in instances_list.read_instance_rows():
        if instance.get("item_type") == "Segment":
            node_a = instance.get("node_at_end_a")
            node_b = instance.get("node_at_end_b")
            if node_a and node_b:
                adjacency[node_a].append(node_b)
                adjacency[node_b].append(node_a)

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
                raise Exception(
                    "Loop detected in formboard graph. Would be cool, but Harnice doesn't support that yet."
                )

    # === Detect dangling/disconnected nodes ===
    all_nodes_in_segments = set(adjacency.keys())
    nodes_without_segments = nodes_from_instances_list - all_nodes_in_segments
    if nodes_without_segments:
        raise Exception(
            f"Dangling nodes with no connections found: {', '.join(sorted(nodes_without_segments))}"
        )

    def bfs(start):
        q = deque([start])
        seen = {start}
        while q:
            n = q.popleft()
            for nbr in adjacency.get(n, []):
                if nbr not in seen:
                    seen.add(nbr)
                    q.append(nbr)
        return seen

    all_nodes = set(adjacency.keys())
    seen_global = set()
    components = []

    for n in all_nodes:
        if n not in seen_global:
            component = bfs(n)
            seen_global |= component
            components.append(component)

    if len(components) > 1:
        formatted_connector_groups = "\n".join(
            f"  - [{', '.join(sorted(c))}]" for c in components
        )
        raise Exception(
            f"Disconnected formboard graph found ({len(components)} connector_groups):\n{formatted_connector_groups}"
        )


def generate_node_coordinates():
    # === Step 1: Load segments and nodes from instances_list ===
    instances = instances_list.read_instance_rows()

    segments = [inst for inst in instances if inst.get("item_type") == "Segment"]
    nodes = [inst for inst in instances if inst.get("item_type") == "Node"]

    # === Step 2: Determine origin node ===
    origin_node = ""
    for seg in segments:
        origin_node = seg.get("node_at_end_a")
        if origin_node:
            break

    print(f"-Origin node: '{origin_node}'")

    # === Step 3: Build graph from segments ===
    graph = {}
    for seg in segments:
        a = seg.get("node_at_end_a")
        b = seg.get("node_at_end_b")
        if a and b:
            graph.setdefault(a, []).append((b, seg))
            graph.setdefault(b, []).append((a, seg))

    # === Step 4: Propagate coordinates ===
    node_coordinates = {origin_node: (0.0, 0.0)}
    queue = deque([origin_node])

    while queue:
        current = queue.popleft()
        current_x, current_y = node_coordinates[current]

        for neighbor, segment in graph.get(current, []):
            if neighbor in node_coordinates:
                continue

            try:
                angle_deg = float(segment.get("absolute_rotation", 0))
                length = float(segment.get("length", 0))
            except ValueError:
                continue

            # Flip the direction if we're traversing from the B-end toward A-end
            if current == segment.get("node_at_end_b"):
                angle_deg = (angle_deg + 180) % 360

            radians = math.radians(angle_deg)
            dx = length * math.cos(radians)
            dy = length * math.sin(radians)

            new_x = round(current_x + dx, 2)
            new_y = round(current_y + dy, 2)
            node_coordinates[neighbor] = (new_x, new_y)
            queue.append(neighbor)

    # === Step 5: Compute and assign average node angles ===
    for node in nodes:
        node_name = node.get("instance_name")
        total_angle = 0
        count = 0

        for seg in segments:
            if (
                seg.get("node_at_end_a") == node_name
                or seg.get("node_at_end_b") == node_name
            ):
                angle_raw = seg.get("absolute_rotation", "")
                angle = float(angle_raw)

                # Flip angle if node is at segment_end_a
                if seg.get("node_at_end_a") == node_name:
                    angle = (angle + 180) % 360

                total_angle += angle
                count += 1

        average_angle = round(total_angle / count, 2) if count else ""
        translate_x, translate_y = node_coordinates.get(node_name, ("", ""))

        instances_list.modify(
            node_name,
            {
                "translate_x": str(translate_x),
                "translate_y": str(translate_y),
                "absolute_rotation": average_angle,
            },
        )

    # === Step 6: Generate PNG ===
    padding = 50
    scale = 96  # pixels per inch
    radius = 5

    # Compute bounding box
    xs = [x for x, y in node_coordinates.values()]
    ys = [y for x, y in node_coordinates.values()]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    width = int((max_x - min_x) * scale + 2 * padding)
    height = int((max_y - min_y) * scale + 2 * padding)

    def map_xy(x, y):
        """Map logical (CAD) coordinates to image coordinates."""
        return (
            int((x - min_x) * scale + padding),
            int(height - ((y - min_y) * scale + padding)),  # flip Y for image
        )

    # Create white canvas
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)

    # Try to get a system font
    try:
        font = ImageFont.truetype("Arial.ttf", 12)
    except OSError:
        font = ImageFont.load_default()

    # --- Draw segments ---
    for seg in segments:
        a, b = seg.get("node_at_end_a"), seg.get("node_at_end_b")
        if a in node_coordinates and b in node_coordinates:
            x1, y1 = map_xy(*node_coordinates[a])
            x2, y2 = map_xy(*node_coordinates[b])

            # Draw line from A to B
            draw.line((x1, y1, x2, y2), fill="black", width=2)

            # --- Draw arrowhead on B side ---
            arrow_length = 25
            arrow_angle = math.radians(25)  # degrees between arrow sides
            angle = math.atan2(y2 - y1, x2 - x1)

            # Compute arrowhead points
            left_x = x2 - arrow_length * math.cos(angle - arrow_angle)
            left_y = y2 - arrow_length * math.sin(angle - arrow_angle)
            right_x = x2 - arrow_length * math.cos(angle + arrow_angle)
            right_y = y2 - arrow_length * math.sin(angle + arrow_angle)

            draw.polygon([(x2, y2), (left_x, left_y), (right_x, right_y)], fill="black")

            # Midpoint label
            mid_x, mid_y = (x1 + x2) / 2, (y1 + y2) / 2
            draw.text(
                (mid_x, mid_y - 10),
                seg.get("instance_name", ""),
                fill="blue",
                font=font,
            )

    # --- Draw nodes ---
    for name, (x, y) in node_coordinates.items():
        cx, cy = map_xy(x, y)
        draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), fill="red")
        draw.text((cx, cy - 15), name, fill="black", font=font, anchor="mm")

    # Legend
    draw.text(
        (padding, height - padding / 2),
        "Arrows point from End A to End B",
        fill="black",
        font=font,
    )

    img.save(fileio.path("formboard graph definition png"), dpi=(96, 96))


def map_instance_to_segments(instance):
    # Ensure you're trying to map an instance that is segment-based.
    if instance.get("location_is_node_or_segment") != "Segment":
        raise ValueError(
            f"You're trying to map a non segment-based instance {instance.get('instance_name')} across segments."
        )

    # Ensure instance has a start and end node
    if instance.get("node_at_end_a") is None or instance.get("node_at_end_b") is None:
        raise ValueError(
            f"Instance {instance.get('instance_name')} has no start or end node."
        )

    # Build graph of segments
    segments = [
        inst
        for inst in instances_list.read_instance_rows()
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

    start_node = instances_list.instance_in_connector_group_with_item_type(
        instances_list.attribute_of(instance.get("node_at_end_a"), "connector_group"),
        "Node",
    )
    if start_node == 0:
        raise ValueError(
            f"No 'Node' type item found in connector group {instances_list.attribute_of(instance.get("instance_name"), "connector_group")}"
        )
    end_node = instances_list.instance_in_connector_group_with_item_type(
        instances_list.attribute_of(instance.get("node_at_end_b"), "connector_group"),
        "Node",
    )
    if end_node == 0:
        raise ValueError(
            f"No 'Node' type item found in connector group {instances_list.attribute_of(instance.get("instance_name"), "connector_group")}"
        )

    start_node = start_node.get("instance_name")
    end_node = end_node.get("instance_name")

    queue = deque([(start_node, [start_node])])
    visited = set()

    while queue:
        current, path = queue.popleft()
        if current in visited:
            continue
        visited.add(current)

        if current == end_node:
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
        raise ValueError(f"No segment path found between {start_node} and {end_node}")

    # Add a new instance for each connected segment
    for seg_name in segment_path:
        instances_list.new_instance(
            f"{instance.get('instance_name')}.{seg_name}",
            {
                "item_type": "Hardware segment",
                "parent_instance": instance.get("instance_name"),
                "parent_csys": seg_name,
                "location_is_node_or_segment": "Segment",
                "length": instances_list.attribute_of(seg_name, "length"),
            },
        )


def make_segment_drawings():
    # =================================================
    # FIRST, UPDATE SEGMENT INSTANCES
    instances = instances_list.read_instance_rows()

    for instance in instances:
        if instance.get("item_type") == "Segment":
            segment_name = instance.get("instance_name", "").strip()
            if not segment_name:
                continue

            try:
                length_in = float(instance.get("length", 0))
                diameter_in = float(instance.get("diameter", 1))
                length = 96 * length_in
                diameter = 96 * diameter_in

                outline_thickness = 0.05 * 96
                centerline_thickness = 0.015 * 96
                half_diameter = diameter / 2

                svg_content = f"""
                <svg xmlns="http://www.w3.org/2000/svg" width="{length}" height="{diameter}" viewBox="0 {-half_diameter} {length} {diameter}">
                    <g id="{instance.get("instance_name")}-contents-start">
                        <line x1="0" y1="0" x2="{length}" y2="0" stroke="black" stroke-width="{diameter}" />
                        <line x1="0" y1="0" x2="{length}" y2="0" stroke="white" stroke-width="{diameter - outline_thickness}" />
                        <line x1="0" y1="0" x2="{length}" y2="0" stroke="black" style="stroke-width:{centerline_thickness};stroke-dasharray:18,18;stroke-dashoffset:0" />
                    </g>
                    <g id="{instance.get("instance_name")}-contents-end"></g>
                </svg>
                """
                segment_dir = os.path.join(
                    fileio.dirpath("generated_instances_do_not_edit"), segment_name
                )
                os.makedirs(segment_dir, exist_ok=True)

                output_filename = os.path.join(
                    segment_dir, f"{segment_name}-drawing.svg"
                )
                with open(output_filename, "w") as svg_file:
                    svg_file.write(svg_content)

            except Exception as e:
                print(f"Error processing segment {segment_name}: {e}")
