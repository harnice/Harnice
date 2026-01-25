# Formboard Utilities
---
##Commands:
*Use the following functions by first importing the module in your script like this: 
```python
from harnice.lists import formboard_utils
```
 then use as written.*
??? info "`formboard_utils.validate_nodes()`"

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

??? info "`formboard_utils.map_instance_to_segments(instance)`"

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

??? info "`formboard_utils.calculate_location(lookup_instance, instances)`"

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

??? info "`formboard_utils.draw_line(from_coords, to_coords, scale=1, from_leader=False, to_leader=True, indent=6, stroke='black', thickness=1)`"

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

