import os
import random
import math
import ast
from collections import defaultdict, deque
from PIL import Image, ImageDraw, ImageFont
from harnice import fileio
from harnice.lists import instances_list, formboard_graph


def validate_nodes():
    """
    Validates and initializes the formboard graph structure.

    This comprehensive function performs multiple tasks:

    1. Ensures the formboard graph definition TSV exists (creates if missing)
    2. Synchronizes nodes from the instances list with the formboard graph
    3. Creates segments if the graph is empty (wheel-spoke for >2 nodes, single segment for 2 nodes)
    4. Adds missing nodes to the graph definition
    5. Removes obsolete nodes and segments
    6. Validates graph structure (no loops, no dangling nodes, single connected component)
    7. Generates node coordinates by propagating from origin
    8. Calculates average node angles based on connected segments
    9. Generates a PNG visualization of the formboard graph

    **Raises:**

    - `ValueError`: If fewer than two nodes are defined.
    - `Exception`: If loops are detected, if nodes have no segments, or if the graph
        has disconnected components.

    """
    # Ensure TSV exists
    if not os.path.exists(fileio.path("formboard graph definition")):
        formboard_graph.new()

    # Collect node names from the instance list
    nodes_from_instances_list = {
        instance.get("instance_name")
        for instance in fileio.read_tsv("instances list")
        if instance.get("item_type") == "node"
    }

    # --- Case 1: No segments exist in formboard definition yet, build from scratch ---
    if not fileio.read_tsv("formboard graph definition"):
        # If there are more than two nodes, make a randomized wheel-spoke graph
        if len(nodes_from_instances_list) > 2:
            origin_node = "node1"
            node_counter = 0
            for instance in fileio.read_tsv("instances list"):
                if instance.get("item_type") == "node":
                    segment_id = instance.get("instance_name") + "_leg"
                    formboard_graph.append(
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
        # If there are exactly two nodes, make a single segment between them
        elif len(nodes_from_instances_list) == 2:
            segment_id = "segment"
            segment_ends = []
            for instance in fileio.read_tsv("instances list"):
                if instance.get("item_type") == "node":
                    segment_ends.append(instance.get("instance_name"))

            formboard_graph.append(
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
        # If there are fewer than two nodes, raise an error
        else:
            raise ValueError("Fewer than two nodes defined, cannot build segments.")

    # --- Case 2: Some nodes from instances list exist in the formboard definition but not all of them ---
    # Extract nodes already involved in segments in formboard definition
    nodes_from_formboard_definition = set()
    for row in fileio.read_tsv("formboard graph definition"):
        nodes_from_formboard_definition.add(row.get("node_at_end_a", ""))
        nodes_from_formboard_definition.add(row.get("node_at_end_b", ""))
    nodes_from_formboard_definition.discard("")

    nodes_from_instances_list_not_in_formboard_def = (
        nodes_from_instances_list - nodes_from_formboard_definition
    )

    if nodes_from_instances_list_not_in_formboard_def:
        for missing_node in nodes_from_instances_list_not_in_formboard_def:
            segment_id = f"{missing_node}_leg"

            node_to_attach_new_leg_to = ""
            for instance in fileio.read_tsv("instances list"):
                if (
                    instance.get("item_type") == "node"
                    and instance.get("instance_name") != missing_node
                ):
                    node_to_attach_new_leg_to = instance.get("instance_name")
                    break

            if not node_to_attach_new_leg_to:
                raise ValueError(
                    f"No existing node found to connect {missing_node} to."
                )

            formboard_graph.append(
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

    # --- Remove any segments that connect to nodes that are both...
    #        only referenced once in the formboard definition and
    #        not in the instances list
    # remove their nodes as well

    segments = fileio.read_tsv("formboard graph definition")
    node_occurrences = defaultdict(int)

    for seg in segments:
        node_occurrences[seg.get("node_at_end_a")] += 1
        node_occurrences[seg.get("node_at_end_b")] += 1

    obsolete_nodes = [
        node
        for node, count in node_occurrences.items()
        if count == 1 and node not in nodes_from_instances_list
    ]

    if obsolete_nodes:
        cleaned_segments = [
            seg
            for seg in segments
            if seg.get("node_at_end_a") not in obsolete_nodes
            and seg.get("node_at_end_b") not in obsolete_nodes
        ]

        # reset the file to header only
        formboard_graph.new()

        # re-append each segment cleanly using your existing append logic
        for seg in cleaned_segments:
            formboard_graph.append(seg["segment_id"], seg)

    # --- Ensure each valid segment from formboard definition is represented in instances list
    for segment in fileio.read_tsv("formboard graph definition"):
        instances_list.new_instance(
            segment.get("segment_id"),
            {
                "item_type": "segment",
                "location_type": "segment",
                "segment_group": segment.get("segment_id"),
                "length": segment.get("length"),
                "diameter": segment.get("diameter"),
                "parent_csys_instance_name": segment.get("node_at_end_a"),
                "parent_csys_outputcsys_name": "origin",
                "node_at_end_a": segment.get("node_at_end_a"),
                "node_at_end_b": segment.get("node_at_end_b"),
                "absolute_rotation": segment.get("angle"),
            },
        )

    # === Ensure each node is represented in instances list ===
    for node in nodes_from_formboard_definition:
        instances_list.new_instance(
            node,
            {
                "item_type": "node",
                "location_type": "node",
                "parent_csys_instance_name": "origin",
                "parent_csys_outputcsys_name": "origin",
            },
            ignore_duplicates=True,
        )

    # === Detect loops ===
    adjacency = defaultdict(list)
    for instance in fileio.read_tsv("instances list"):
        if instance.get("item_type") == "segment":
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

    # === Find nodes that are not connected to any segments ===
    all_nodes_in_segments = set(adjacency.keys())
    nodes_without_segments = nodes_from_instances_list - all_nodes_in_segments
    if nodes_without_segments:
        raise Exception(
            f"Dangling nodes with no connections found: {', '.join(sorted(nodes_without_segments))}"
        )

    # === Ensure each segment is part of the same graph (i.e. no disconnected components) ===
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

    # GENERATE NODE COORDINATES

    # === Step 1: Reload from instances_list ===
    instances = fileio.read_tsv("instances list")

    segments = [inst for inst in instances if inst.get("item_type") == "segment"]
    nodes = [inst for inst in instances if inst.get("item_type") == "node"]

    # === Step 2: Determine origin node ===
    origin_node = ""
    for seg in segments:
        origin_node = seg.get("node_at_end_a")
        if origin_node:
            break

    print(f"-origin node: '{origin_node}'")

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
        sum_x, sum_y = 0.0, 0.0
        count = 0

        for seg in segments:
            if (
                seg.get("node_at_end_a") == node_name
                or seg.get("node_at_end_b") == node_name
            ):
                angle_to_add_raw = seg.get("absolute_rotation", "")
                if not angle_to_add_raw:
                    continue
                angle_to_add = float(angle_to_add_raw)

                # Flip 180° if node is at segment_end_b
                if seg.get("node_at_end_b") == node_name:
                    angle_to_add = (angle_to_add + 180) % 360

                # Convert degrees → radians for trig functions
                angle_rad = math.radians(angle_to_add)
                sum_x += math.cos(angle_rad)
                sum_y += math.sin(angle_rad)
                count += 1

        if count:
            # Flip 180° (connector points away from average cable vector)
            avg_x, avg_y = -sum_x, -sum_y

            # Compute angle in degrees, normalized to [0, 360)
            average_angle = math.degrees(math.atan2(avg_y, avg_x)) % 360

            # Round to nearest 0.01 degree
            average_angle = round(average_angle, 2)
        else:
            average_angle = ""

        translate_x, translate_y = node_coordinates.get(node_name, ("", ""))

        instances_list.modify(
            node_name,
            {
                "translate_x": str(translate_x),
                "translate_y": str(translate_y),
                "absolute_rotation": average_angle,
                "parent_csys_instance_name": "origin",
                "parent_csys_outputcsys_name": "origin",
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
    """
    Maps a segment-based instance across multiple segments using pathfinding.

    Takes an instance that spans between two nodes and creates segment-specific
    instances for each segment in the path between those nodes. Uses breadth-first
    search to find the path through the segment graph, then creates new instances
    for each segment with the appropriate direction and order.

    **Note:** The function actually maps to nodes in the same connector group as the
    "end nodes". If your to/from nodes are `item_type=="Cavity"`, for example, this
    function will return paths of segments between the `item_type=="node"` instances
    where those cavities are located.

    **Args:**

    - `instance` (dict): Instance dictionary with `location_type="segment"` that has
        `node_at_end_a` and `node_at_end_b` defined.

    **Raises:**

    - `ValueError`: If the instance is not segment-based, if endpoints are missing,
        if endpoints are not nodes, or if no path is found between the nodes.
    """
    # note to user: we're actually mapping to nodes in same connector group as the "end nodes".
    # so if your to/from nodes are item_type==Cavity, for example, this function will return paths of segments
    # between the item_type==node instance where those cavities are

    # Ensure you're trying to map an instance that is segment-based.
    if instance.get("location_type") != "segment":
        raise ValueError(
            f"You're trying to map a non segment-based instance {instance.get('instance_name')} across segments."
        )

    # Ensure instance has a start and end node
    if instance.get("node_at_end_a") is None or instance.get("node_at_end_b") is None:
        raise ValueError(
            f"Instance {instance.get('instance_name')} has no start or end node."
        )

    # Ensure each endpoint is actually location_type==node
    if (
        instances_list.attribute_of(instance.get("node_at_end_a"), "location_type")
        != "node"
    ):
        raise ValueError(
            f"While mapping '{instance.get("instance_name")}' to segments, location type of {instance.get('node_at_end_a')} is not a node."
        )
    if (
        instances_list.attribute_of(instance.get("node_at_end_b"), "location_type")
        != "node"
    ):
        raise ValueError(
            f"While mapping '{instance.get("instance_name")}' to segments, location type of {instance.get('node_at_end_b')} is not a node."
        )

    # Resolve the node (item_type=="node") for each end's connector group
    start_node_obj = instances_list.instance_in_connector_group_with_item_type(
        instances_list.attribute_of(instance.get("node_at_end_a"), "connector_group"),
        "node",
    )
    try:
        if start_node_obj == 0:
            raise ValueError(
                f"No 'node' type item found in connector group {instance.get('connector_group')}"
            )
        if start_node_obj > 1:
            raise ValueError(
                f"Multiple 'node' type items found in connector group {instance.get('connector_group')}"
            )
    except TypeError:
        pass

    end_node_obj = instances_list.instance_in_connector_group_with_item_type(
        instances_list.attribute_of(instance.get("node_at_end_b"), "connector_group"),
        "node",
    )
    try:
        if end_node_obj == 0:
            raise ValueError(
                f"No 'node' type item found in connector group {instance.get('connector_group')}"
            )
        if end_node_obj > 1:
            raise ValueError(
                f"Multiple 'node' type items found in connector group {instance.get('connector_group')}"
            )
    except TypeError:
        pass

    # Build graph of segments
    segments = [
        inst
        for inst in fileio.read_tsv("instances list")
        if inst.get("item_type") == "segment"
    ]

    graph = {}
    segment_lookup = {}  # frozenset({A, B}) -> seg_name
    seg_endpoints = {}  # seg_name -> (A, B) with stored orientation

    for seg in segments:
        a = seg.get("node_at_end_a")
        b = seg.get("node_at_end_b")
        seg_name = seg.get("instance_name")
        if not a or not b:
            continue
        graph.setdefault(a, set()).add(b)
        graph.setdefault(b, set()).add(a)
        segment_lookup[frozenset([a, b])] = seg_name
        seg_endpoints[seg_name] = (a, b)

    # Re-fetch start/end nodes as instance_names
    start_node_obj = instances_list.instance_in_connector_group_with_item_type(
        instances_list.attribute_of(instance.get("node_at_end_a"), "connector_group"),
        "node",
    )
    if start_node_obj == 0:
        raise ValueError(
            f"No 'node' type item found in connector group {instances_list.attribute_of(instance.get('instance_name'), 'connector_group')}"
        )

    end_node_obj = instances_list.instance_in_connector_group_with_item_type(
        instances_list.attribute_of(instance.get("node_at_end_b"), "connector_group"),
        "node",
    )
    if end_node_obj == 0:
        raise ValueError(
            f"No 'node' type item found in connector group {instances_list.attribute_of(instance.get('instance_name'), 'connector_group')}"
        )

    start_node = start_node_obj.get("instance_name")
    end_node = end_node_obj.get("instance_name")

    # ---- BFS that records per-edge segment + direction ----
    # pred[node] = (prev_node, seg_name, direction)
    pred = {}
    visited = set()
    queue = deque([start_node])
    visited.add(start_node)

    while queue:
        u = queue.popleft()
        if u == end_node:
            break
        for v in graph.get(u, []):
            if v in visited:
                continue
            seg_name = segment_lookup.get(frozenset([u, v]))
            if not seg_name:
                continue
            a_end, b_end = seg_endpoints[seg_name]
            direction = "ab" if (u == a_end and v == b_end) else "ba"
            pred[v] = (u, seg_name, direction)
            visited.add(v)
            queue.append(v)

    if end_node not in pred and start_node != end_node:
        raise ValueError(f"No segment path found between {start_node} and {end_node}")

    # Reconstruct (seg_name, direction) list from predecessors
    segment_steps = []
    if start_node != end_node:
        cur = end_node
        while cur != start_node:
            prev, seg_name, direction = pred[cur]
            segment_steps.append((seg_name, direction))
            cur = prev
        segment_steps.reverse()
    # -------------------------------------------------------

    # Add a new instance for each connected segment, preserving per-segment direction
    i = 1
    for seg_name, direction in segment_steps:
        instances_list.new_instance(
            f"{instance.get('instance_name')}.{seg_name}",
            {
                "item_type": f"{instance.get('item_type')}-segment",
                "parent_instance": instance.get("instance_name"),
                "segment_group": seg_name,
                "segment_order": f"{i}-{direction}",
                "parent_csys": seg_name,
                "location_type": "segment",
                "channel_group": instance.get("channel_group"),
                "circuit_id": instance.get("circuit_id"),
                "circuit_port_number": instance.get("circuit_port_number"),
                "cable_group": instance.get("cable_group"),
                "cable_container": instance.get("cable_container"),
                "cable_identifier": instance.get("cable_identifier"),
                "appearance": instance.get("appearance"),
                "this_net_from_device_refdes": instance.get(
                    "this_net_from_device_refdes"
                ),
                "this_net_from_device_channel_id": instance.get(
                    "this_net_from_device_channel_id"
                ),
                "this_net_from_device_connector_name": instance.get(
                    "this_net_from_device_connector_name"
                ),
                "this_net_to_device_refdes": instance.get("this_net_to_device_refdes"),
                "this_net_to_device_channel_id": instance.get(
                    "this_net_to_device_channel_id"
                ),
                "this_net_to_device_connector_name": instance.get(
                    "this_net_to_device_connector_name"
                ),
                "this_channel_from_device_refdes": instance.get(
                    "this_channel_from_device_refdes"
                ),
                "this_channel_from_device_channel_id": instance.get(
                    "this_channel_from_device_channel_id"
                ),
                "this_channel_to_device_refdes": instance.get(
                    "this_channel_to_device_refdes"
                ),
                "this_channel_to_device_channel_id": instance.get(
                    "this_channel_to_device_channel_id"
                ),
                "this_channel_from_channel_type": instance.get(
                    "this_channel_from_channel_type"
                ),
                "this_channel_to_channel_type": instance.get(
                    "this_channel_to_channel_type"
                ),
                "signal_of_channel_type": instance.get("signal_of_channel_type"),
                "length": instances_list.attribute_of(seg_name, "length"),
            },
        )
        i += 1


def calculate_location(lookup_instance, instances):
    """
    Calculates world coordinates for an instance by accumulating transforms through the CSYS chain.

    Traces the coordinate system hierarchy from the instance up to the origin, accumulating
    translations and rotations at each level. Applies child coordinate system transforms,
    instance translations, and rotations to compute the final world position and angle.

    The function handles both Cartesian (`x`, `y`) and polar (`distance`, `angle`) coordinate
    specifications for child coordinate systems. Absolute rotation overrides accumulated rotation.

    **Args:**

    - `lookup_instance` (dict): The instance dictionary to calculate coordinates for.
    - `instances` (list): List of all instance dictionaries needed to resolve the parent chain.

    **Returns:**

    - `tuple`: A tuple of `(x_pos, y_pos, angle)` representing the world coordinates and
        rotation angle in degrees.

    **Raises:**
    
    - `ValueError`: If parent coordinate system information is missing or invalid, or
        if parent instances cannot be found in the instances list.
    """
    # ------------------------------------------------------------------
    # Normalize csys_children: ensure all rows contain real dicts
    # ------------------------------------------------------------------
    for instance in instances:
        raw_children = instance.get("csys_children")
        try:
            if isinstance(raw_children, str) and raw_children:
                csys_children = ast.literal_eval(raw_children)
            else:
                csys_children = raw_children or {}
        except Exception:
            csys_children = {}
        instance["csys_children"] = csys_children

    # ------------------------------------------------------------------
    # Build the CSYS parent chain (from item → origin)
    # ------------------------------------------------------------------
    chain = []

    current = lookup_instance

    while True:
        # Find the current instance in the raw instances list
        parent_csys_instance_name = None
        parent_csys_outputcsys_name = None

        for instance in instances:
            if instance.get("instance_name") == current.get("instance_name"):
                parent_csys_instance_name = instance.get("parent_csys_instance_name")
                parent_csys_outputcsys_name = instance.get(
                    "parent_csys_outputcsys_name"
                )
                chain.append(instance)
                break

        # Stop once we reach the origin csys
        if current.get("instance_name") == "origin":
            break

        # Required-parent validation
        if parent_csys_instance_name is None:
            raise ValueError(
                f"Instance '{current.get('instance_name')}' missing parent_csys_instance_name"
            )
        if not parent_csys_instance_name:
            raise ValueError(
                f"Instance '{current.get('instance_name')}' parent_csys_instance_name blank"
            )
        if not parent_csys_outputcsys_name:
            raise ValueError(
                f"Instance '{current.get('instance_name')}' parent_csys_outputcsys_name blank"
            )

        # Resolve parent instance
        parent_csys_instance = None
        for instance in instances:
            if instance.get("instance_name") == parent_csys_instance_name:
                parent_csys_instance = instance
                break
        else:
            raise ValueError(
                f"Instance '{parent_csys_instance_name}' not found in instances list"
            )

        current = parent_csys_instance

    # Reverse chain: now runs origin → lookup_item
    chain = list(reversed(chain))

    # ------------------------------------------------------------------
    # Accumulate transforms along chain
    # ------------------------------------------------------------------
    x_pos = 0.0
    y_pos = 0.0
    angle = 0.0

    for chainlink in chain:

        # ==================================================================
        #   Resolve CHILD CSYS (the transform from parent output csys)
        # ==================================================================
        relevant_csys_child = None

        # Find the chainlink's parent instance and extract its csys_children
        for instance in instances:
            if instance.get("instance_name") == chainlink.get(
                "parent_csys_instance_name"
            ):
                if instance.get("csys_children") != {}:
                    relevant_csys_child = instance["csys_children"].get(
                        chainlink.get("parent_csys_outputcsys_name")
                    )
                else:
                    relevant_csys_child = {}
                break

        angle_old = angle
        dx = 0.0
        dy = 0.0

        # ------------------------------------------------------------------
        # Child CSYS: translation component
        # ------------------------------------------------------------------
        if relevant_csys_child is not None:

            # x/y explicit translation
            if relevant_csys_child.get("x") not in [
                "",
                None,
            ] and relevant_csys_child.get("y") not in ["", None]:
                dx = float(relevant_csys_child.get("x"))
                dy = float(relevant_csys_child.get("y"))

            # polar translation
            elif relevant_csys_child.get("distance") not in [
                "",
                None,
            ] and relevant_csys_child.get("angle") not in ["", None]:
                dist = float(relevant_csys_child.get("distance"))
                ang = math.radians(float(relevant_csys_child.get("angle")))
                dx = dist * math.cos(ang)
                dy = dist * math.sin(ang)

            # Child CSYS rotation
            if relevant_csys_child.get("rotation") not in ["", None]:
                angle += float(relevant_csys_child.get("rotation"))

        # ------------------------------------------------------------------
        # Apply rotated dx/dy into world coordinates
        # ------------------------------------------------------------------
        dx_old = dx
        dy_old = dy

        x_pos += dx_old * math.cos(math.radians(angle_old)) - dy_old * math.sin(
            math.radians(angle_old)
        )
        y_pos += dx_old * math.sin(math.radians(angle_old)) + dy_old * math.cos(
            math.radians(angle_old)
        )

        # ------------------------------------------------------------------
        # Chainlink's local transform fields
        # ------------------------------------------------------------------
        if chainlink.get("translate_x") not in ["", None]:
            x_pos += float(chainlink.get("translate_x"))

        if chainlink.get("translate_y") not in ["", None]:
            y_pos += float(chainlink.get("translate_y"))

        if chainlink.get("rotate_csys") not in ["", None]:
            angle += float(chainlink.get("rotate_csys"))

        # Absolute rotation overrides accumulated rotation
        if chainlink.get("absolute_rotation") not in ["", None]:
            angle = float(chainlink.get("absolute_rotation"))

    # ------------------------------------------------------------------
    # Final world coordinates
    # ------------------------------------------------------------------
    return x_pos, y_pos, angle


def draw_line(
    from_coords,
    to_coords,
    scale=1,
    from_leader=False,
    to_leader=True,
    indent=6,
    stroke="black",
    thickness=1,
):
    """
    Generates SVG markup for a line with optional arrowheads.

    Creates SVG elements for a line connecting two points, with optional arrowheads
    at either or both ends. Coordinates are converted from inches to pixels (96 dpi)
    with Y-axis flipped for SVG coordinate system.

    **Args:**
    - `from_coords` (tuple): Starting coordinates as `(x, y)` in inches.
    - `to_coords` (tuple): Ending coordinates as `(x, y)` in inches.
    - `scale` (float, optional): Scale factor for arrowhead size and line thickness. Defaults to `1`.
    - `from_leader` (bool, optional): If `True`, draw an arrowhead at the start. Defaults to `False`.
    - `to_leader` (bool, optional): If `True`, draw an arrowhead at the end. Defaults to `True`.
    - `indent` (int, optional): Unused parameter (maintained for compatibility). Defaults to `6`.
    - `stroke` (str, optional): Stroke color. Defaults to `"black"`.
    - `thickness` (float, optional): Line thickness in pixels (before scaling). Defaults to `1`.

    **Returns:**
    - `str`: SVG markup string containing the line and arrowhead elements, or empty
        string if coordinates are identical (zero-length line).
    """
    # Convert inches → px (and flip Y)
    fx, fy = from_coords[0] * 96, from_coords[1] * -96
    tx, ty = to_coords[0] * 96, to_coords[1] * -96

    # Geometry for arrowheads
    dx = tx - fx
    dy = ty - fy
    line_len = math.hypot(dx, dy)

    if line_len == 0:
        return ""  # cannot draw arrowheads on zero-length line

    # Normalize direction vector
    ux = dx / line_len
    uy = dy / line_len

    # Arrowhead size (scaled)
    arrow_len = 8 / scale
    arrow_wid = 6 / scale

    svg_parts = []

    # -------------------------
    # Draw main line
    # -------------------------
    svg_parts.append(
        f'<line x1="{fx}" y1="{fy}" x2="{tx}" y2="{ty}" '
        f'stroke="{stroke}" stroke-width="{thickness/scale}"/>'
    )

    # -------------------------
    # Arrowhead helper
    # -------------------------
    def arrowhead(px, py, ux, uy):
        # Base of arrowhead is at (px, py)
        # Two side points:
        # Rotate ±90° for perpendicular direction
        perp_x = -uy
        perp_y = ux

        p1x = px - ux * arrow_len + perp_x * (arrow_wid / 2)
        p1y = py - uy * arrow_len + perp_y * (arrow_wid / 2)

        p2x = px - ux * arrow_len - perp_x * (arrow_wid / 2)
        p2y = py - uy * arrow_len - perp_y * (arrow_wid / 2)

        return (
            f'<polygon points="'
            f'{px},{py} {p1x},{p1y} {p2x},{p2y}" '
            f'fill="{stroke}"/>'
        )

    # -------------------------
    # Arrow at TO end
    # -------------------------
    if to_leader:
        svg_parts.append(arrowhead(tx, ty, ux, uy))

    # -------------------------
    # Arrow at FROM end
    # reverse direction for correct orientation
    # -------------------------
    if from_leader:
        svg_parts.append(arrowhead(fx, fy, -ux, -uy))

    return "".join(svg_parts)
