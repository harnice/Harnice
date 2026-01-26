# import your modules here
import os
import re
import json
import math
from typing import Dict, Set, Tuple, List
from harnice import fileio, state
from PIL import Image, ImageDraw, ImageFont
from harnice.utils import svg_utils

# describe your args here. comment them out and do not officially define because they are called via runpy,
# for example, the caller feature_tree should define the arguments like this:
# feature_tree_utils.run_macro(
#    "kicad_sch_parser",
#    "harness_artifacts",
#    "https://github.com/harnice/harnice-library-public",
#    artifact_id="kicad-schematic-parser",
# )
#
# Expected args (injected by caller or defaulted below):
# artifact_id: str (optional override)
# base_directory: str | None  (optional override)
# item_type: filter placed on the instances list in the "item_type" column, filtering only instances we're trying to plot here. for example, "channel" or "circuit",

# define the artifact_id of this macro (treated the same as part number). should match the filename.
artifact_id = "kicad_sch_parser"

# KiCad internal units to inches conversion
# KiCad v6+ schematics store coordinates in millimeters
# Need to convert mm to inches: 1 inch = 25.4 mm
KICAD_UNIT_SCALE = 1.0 / 25.4  # Convert from millimeters to inches

# Precision for final output (number of decimal places)
OUTPUT_PRECISION = 5

print_circles_and_dots = True

# =============== PATHS ===================================================================================
def macro_file_structure():
    return {
        f"{artifact_id}-graph.json": "graph of nodes and segments",
        f"{artifact_id}-schematic-visualization.png": "schematic visualization png",
        f"{artifact_id}-kicad-direct-export": { # i think this is because kicad exports svgs into a directory with the same name as the target file
            f"{state.partnumber('pn')}-{state.partnumber('rev')}.svg": "kicad direct export svg",
        },
        "overlay_svgs":{
            f"{artifact_id}-net-overlay.svg": "net overlay svg",
        }
    }

def file_structure():
    return {
        "kicad": {
            f"{state.partnumber('pn-rev')}.kicad_sch": "kicad sch",
        }
    }

# this runs automatically and is used to assign a default base directory if it is not called by the caller.
if base_directory == None:
    base_directory = os.path.join("instance_data", "macro", artifact_id)

def path(target_value):
    return fileio.path(
        target_value,
        structure_dict=macro_file_structure(),
        base_directory=base_directory,
    )

def dirpath(target_value):
    return fileio.dirpath(
        target_value,
        structure_dict=macro_file_structure(),
        base_directory=base_directory,
    )

os.makedirs(dirpath(None), exist_ok=True)
os.makedirs(dirpath("overlay_svgs"), exist_ok=True)

# =============== PARSER CLASS =============================================================================

class KiCadSchematicParser:
    def __init__(self, filepath):
        with open(filepath, 'r') as f:
            self.content = f.read()
        
    def parse(self):
        """Parse all data from the schematic"""
        pin_locations_of_lib_symbols = self._parse_lib_symbols()
        locations_of_lib_instances = self._parse_lib_instances()
        wire_locations = self._parse_wires()
        
        return pin_locations_of_lib_symbols, locations_of_lib_instances, wire_locations
    
    def _parse_lib_symbols(self) -> Dict:
        """
        Parse lib_symbols section to extract pin locations for each library symbol.
        Returns:
        {
            lib_id: {
                pin_name: {
                    'x_loc': xxxx,
                    'y_loc': xxxx
                }
            }
        }
        """
        pin_locations_of_lib_symbols = {}
        
        # Find the lib_symbols section
        lib_symbols_match = re.search(r'\(lib_symbols(.*?)\n\t\)', self.content, re.DOTALL)
        if not lib_symbols_match:
            return pin_locations_of_lib_symbols
        
        lib_symbols_section = lib_symbols_match.group(1)
        
        # Pattern to match each symbol definition
        # Matches: (symbol "lib_id" ... )
        symbol_pattern = r'\(symbol\s+"([^"]+)"(.*?)(?=\n\t\t\(symbol\s+"|$)'
        
        for symbol_match in re.finditer(symbol_pattern, lib_symbols_section, re.DOTALL):
            lib_id = symbol_match.group(1)
            symbol_body = symbol_match.group(2)
            
            # Initialize this lib_id if we haven't seen it yet
            if lib_id not in pin_locations_of_lib_symbols:
                pin_locations_of_lib_symbols[lib_id] = {}
            
            # Find all pins in this symbol definition
            pin_pattern = r'\(pin\s+\w+\s+\w+\s+\(at\s+([-\d.]+)\s+([-\d.]+)\s+(\d+)\)\s+\(length\s+([-\d.]+)\).*?\(name\s+"([^"]+)"'
            
            for pin_match in re.finditer(pin_pattern, symbol_body, re.DOTALL):
                x, y, angle, length, pin_name = pin_match.groups()
                x, y = float(x), float(y)
                
                pin_locations_of_lib_symbols[lib_id][pin_name] = {
                    'x_loc': x,
                    'y_loc': y
                }
        
        return pin_locations_of_lib_symbols
    
    def _parse_lib_instances(self) -> Dict:
        """
        Parse symbol instances to extract their locations and references.
        Returns:
        {
            refdes: {
                'x': xxxx,
                'y': xxxx,
                'rotate': xxxx,
                'lib_id': xxxx
            }
        }
        """
        locations_of_lib_instances = {}
        
        # Pattern to match symbol instances
        # (symbol (lib_id "...") (at x y rotation) ... (property "Reference" "refdes"
        symbol_instance_pattern = r'\(symbol\s+\(lib_id\s+"([^"]+)"\)\s+\(at\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\)(.*?)\(property "Reference"\s+"([^"]+)"'
        
        for match in re.finditer(symbol_instance_pattern, self.content, re.DOTALL):
            lib_id, x, y, rotate, body, refdes = match.groups()
            
            locations_of_lib_instances[refdes] = {
                'x': float(x),
                'y': float(y),
                'rotate': float(rotate),
                'lib_id': lib_id
            }
        
        return locations_of_lib_instances
    
    def _parse_wires(self) -> Dict:
        """
        Parse wire segments.
        Returns:
        {
            wire_uuid: {
                'a_x': xxxx,
                'a_y': xxxx,
                'b_x': xxxx,
                'b_y': xxxx
            }
        }
        """
        wire_locations = {}
        
        # Pattern: (wire (pts (xy x1 y1) (xy x2 y2)) ... (uuid "...")
        wire_pattern = r'\(wire\s+\(pts\s+\(xy\s+([-\d.]+)\s+([-\d.]+)\)\s+\(xy\s+([-\d.]+)\s+([-\d.]+)\)\s+\)[\s\S]*?\(uuid\s+"([^"]+)"\)'
        
        for match in re.finditer(wire_pattern, self.content):
            x1, y1, x2, y2, uuid = match.groups()
            
            wire_locations[uuid] = {
                'a_x': float(x1),
                'a_y': float(y1),
                'b_x': float(x2),
                'b_y': float(y2)
            }
        
        return wire_locations

def rotate_point(x, y, angle_degrees):
    """Rotate a point by angle in degrees"""
    angle_rad = math.radians(angle_degrees)
    cos_a = math.cos(angle_rad)
    sin_a = math.sin(angle_rad)
    
    new_x = x * cos_a - y * sin_a
    new_y = x * sin_a + y * cos_a
    
    return new_x, new_y

def compile_pin_locations(pin_locations_of_lib_symbols, locations_of_lib_instances):
    """
    Compile absolute pin locations for each instance.
    Returns:
    {
        box_refdes: {
            pin_name: {
                'x_loc': xxxx,
                'y_loc': xxxx
            }
        }
    }
    """
    pin_locations = {}
    
    for refdes, instance_info in locations_of_lib_instances.items():
        lib_id = instance_info['lib_id']
        instance_x = instance_info['x']
        instance_y = instance_info['y']
        instance_rotate = instance_info['rotate']
        
        # Check if we have pin data for this lib_id
        if lib_id not in pin_locations_of_lib_symbols:
            print(f"Warning: No pin data found for lib_id '{lib_id}' (used by {refdes})")
            continue
        
        pin_locations[refdes] = {}
        
        # For each pin in the library symbol, calculate its absolute position
        for pin_name, pin_info in pin_locations_of_lib_symbols[lib_id].items():
            pin_x_rel = pin_info['x_loc']
            pin_y_rel = pin_info['y_loc']
            
            # Rotate the pin relative position by the instance rotation
            rotated_x, rotated_y = rotate_point(pin_x_rel, pin_y_rel, instance_rotate)
            
            # KiCad Y coordinate is inverted in symbol definitions
            # Y increases downward in schematic, but symbol coords use upward Y
            absolute_x = instance_x + rotated_x
            absolute_y = instance_y - rotated_y  # SUBTRACT Y
            
            pin_locations[refdes][pin_name] = {
                'x_loc': absolute_x,
                'y_loc': absolute_y
            }
    
    return pin_locations

def round_and_scale_coordinates(data, scale_factor):
    """
    Round coordinates to nearest 0.1 mil, then scale to inches, then round to output precision.
    Recursively processes nested dictionaries.
    """
    if isinstance(data, dict):
        processed = {}
        for key, value in data.items():
            if key in ['x_loc', 'y_loc', 'x', 'y', 'a_x', 'a_y', 'b_x', 'b_y']:
                # Round to nearest 0.1 mil (multiply by 10, round, divide by 10)
                rounded_mils = round(value * 10) / 10
                # Convert to inches
                inches = rounded_mils * scale_factor
                # Round to output precision to avoid floating point artifacts
                processed[key] = round(inches, OUTPUT_PRECISION)
            else:
                processed[key] = round_and_scale_coordinates(value, scale_factor)
        return processed
    else:
        return data

def build_graph(pin_locations_scaled, wire_locations_scaled):
    """
    Build a graph from pin locations and wire locations.
    
    Returns:
    {
        'nodes': {
            node_uuid: {
                'x': xxxx,
                'y': xxxx
            }
        },
        'segments': {
            wire_uuid: {
                'node_at_end_a': node_uuid,
                'node_at_end_b': node_uuid
            }
        }
    }
    """
    nodes = {}
    segments = {}
    
    TOLERANCE = 0.01
    
    def round_coord(value):
        return round(value / TOLERANCE) * TOLERANCE
    
    def location_key(x, y):
        return (round_coord(x), round_coord(y))
    
    location_to_node = {}
    junction_counter = 0
    
    # Step 1: Add all pins as nodes
    for refdes, pins in pin_locations_scaled.items():
        for pin_name, coords in pins.items():
            node_uuid = f"{refdes}.{pin_name}"
            x = coords['x_loc']
            y = coords['y_loc']
            
            nodes[node_uuid] = {
                'x': round(x, OUTPUT_PRECISION),
                'y': round(y, OUTPUT_PRECISION)
            }
            
            loc_key = location_key(x, y)
            location_to_node[loc_key] = node_uuid
    
    # Step 2: Process wires and create junction nodes where needed
    for wire_uuid, wire_coords in wire_locations_scaled.items():
        a_x = wire_coords['a_x']
        a_y = wire_coords['a_y']
        b_x = wire_coords['b_x']
        b_y = wire_coords['b_y']
        
        a_key = location_key(a_x, a_y)
        b_key = location_key(b_x, b_y)
        
        # Get or create node for end A
        if a_key not in location_to_node:
            junction_uuid = f"wirejunction-{junction_counter}"
            junction_counter += 1
            nodes[junction_uuid] = {
                'x': round(a_x, OUTPUT_PRECISION),
                'y': round(a_y, OUTPUT_PRECISION)
            }
            location_to_node[a_key] = junction_uuid
        
        a_node = location_to_node[a_key]
        
        # Get or create node for end B
        if b_key not in location_to_node:
            junction_uuid = f"wirejunction-{junction_counter}"
            junction_counter += 1
            nodes[junction_uuid] = {
                'x': round(b_x, OUTPUT_PRECISION),
                'y': round(b_y, OUTPUT_PRECISION)
            }
            location_to_node[b_key] = junction_uuid
        
        b_node = location_to_node[b_key]
        
        segments[wire_uuid] = {
            'node_at_end_a': a_node,
            'node_at_end_b': b_node
        }
    
    return {
        'nodes': nodes,
        'segments': segments
    }

def generate_schematic_png(graph, output_path):
    """
    Generate a PNG visualization of the schematic graph.
    
    Args:
        graph: Dictionary with 'nodes' and 'segments'
        output_path: Path to save the PNG file
    """
    nodes = graph['nodes']
    segments = graph['segments']
    
    if not nodes:
        print("Warning: No nodes to visualize")
        return
    
    # Parameters for standard letter size sheet
    dpi = 1000  # High resolution
    sheet_width_inches = 11  # Letter size landscape
    sheet_height_inches = 8.5
    width = int(sheet_width_inches * dpi)
    height = int(sheet_height_inches * dpi)
    
    # Visual parameters (in inches, then converted to pixels)
    pin_radius_inches = 0.033  # ~0.067in diameter (1/3 of 0.2in)
    junction_radius_inches = 0.033
    font_size_inches = 0.05  # 1/3 of 0.15in
    wire_font_size_inches = 0.05 / 3  # 1/3 of node font size
    arrow_length_inches = 0.067  # 1/3 of 0.2in
    line_width_inches = 0.02
    
    # Convert to pixels
    pin_radius = int(pin_radius_inches * dpi)
    junction_radius = int(junction_radius_inches * dpi)
    font_size = int(font_size_inches * dpi)
    wire_font_size = int(wire_font_size_inches * dpi)
    arrow_length = int(arrow_length_inches * dpi)
    line_width = max(1, int(line_width_inches * dpi))
    
    margin_inches = 0.5  # Margin from sheet edge
    margin_pixels = int(margin_inches * dpi)
    
    # Extract node coordinates (already in inches from the parser)
    node_coordinates = {name: (info['x'], info['y']) for name, info in nodes.items()}
    
    # Compute bounding box of actual content
    xs = [x for x, y in node_coordinates.values()]
    ys = [y for x, y in node_coordinates.values()]
    content_min_x, content_max_x = min(xs), max(xs)
    content_min_y, content_max_y = min(ys), max(ys)
    
    # KiCad coordinates: origin is typically at top-left, Y increases downward
    # We'll map KiCad coordinates directly to sheet space
    def map_xy(x, y):
        """Map KiCad coordinates (in inches) to image pixel coordinates."""
        # X: directly map from left with margin
        pixel_x = int(x * dpi + margin_pixels)
        # Y: KiCad Y increases downward, image Y increases downward, so direct mapping
        pixel_y = int(y * dpi + margin_pixels)
        return (pixel_x, pixel_y)
    
    # Create white canvas
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)
    
    # Try to get a system font with appropriate size
    try:
        font = ImageFont.truetype("Arial.ttf", font_size)
        wire_font = ImageFont.truetype("Arial.ttf", wire_font_size)
        legend_font = ImageFont.truetype("Arial.ttf", font_size)
    except OSError:
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
            wire_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", wire_font_size)
            legend_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
        except OSError:
            font = ImageFont.load_default()
            wire_font = ImageFont.load_default()
            legend_font = ImageFont.load_default()
    
    # --- Draw segments (wires) ---
    for wire_uuid, seg_info in segments.items():
        node_a = seg_info.get("node_at_end_a")
        node_b = seg_info.get("node_at_end_b")
        
        if node_a in node_coordinates and node_b in node_coordinates:
            x1, y1 = map_xy(*node_coordinates[node_a])
            x2, y2 = map_xy(*node_coordinates[node_b])
            
            # Draw line from A to B
            draw.line((x1, y1, x2, y2), fill="black", width=line_width)
            
            # Draw arrow at end B to show direction
            arrow_angle = math.radians(25)
            
            angle = math.atan2(y2 - y1, x2 - x1)
            
            # Compute arrowhead points
            left_x = x2 - arrow_length * math.cos(angle - arrow_angle)
            left_y = y2 - arrow_length * math.sin(angle - arrow_angle)
            right_x = x2 - arrow_length * math.cos(angle + arrow_angle)
            right_y = y2 - arrow_length * math.sin(angle + arrow_angle)
            
            draw.polygon([(x2, y2), (left_x, left_y), (right_x, right_y)], fill="blue")
            
            # Label wire with UUID at center of the wire (smaller font)
            center_x = (x1 + x2) / 2
            center_y = (y1 + y2) / 2
            wire_label_offset = int(0.075 * dpi)  # Same offset as node labels
            draw.text((center_x, center_y - wire_label_offset), wire_uuid, fill="blue", font=wire_font, anchor="mm")
    
    # --- Draw nodes ---
    for name, (x, y) in node_coordinates.items():
        cx, cy = map_xy(x, y)
        
        # Draw all nodes as identical circles (same style for pins and junctions)
        draw.ellipse(
            (cx - pin_radius, cy - pin_radius, 
             cx + pin_radius, cy + pin_radius),
            fill="red",
            outline="darkred",
            width=line_width
        )
        
        # Label all nodes with their names (closer to the node)
        label_offset = int(0.075 * dpi)  # 0.075 inch above the node (half of previous distance)
        draw.text((cx, cy - label_offset), name, fill="black", font=font, anchor="mm")
    
    # Add legend at the bottom of the sheet with visual examples
    legend_y = height - int(0.4 * dpi)  # 0.4 inches from bottom
    legend_x = margin_pixels
    
    # Draw example node (circle - used for all nodes)
    example_node_x = legend_x + int(0.15 * dpi)
    draw.ellipse(
        (example_node_x - pin_radius, legend_y - pin_radius,
         example_node_x + pin_radius, legend_y + pin_radius),
        fill="red",
        outline="darkred",
        width=line_width
    )
    draw.text((example_node_x + int(0.2 * dpi), legend_y), "= Node (identified by label)", 
              fill="black", font=legend_font, anchor="lm")
    
    # Draw example wire with arrow
    example_wire_x = legend_x + int(3.5 * dpi)
    wire_start_x = example_wire_x
    wire_end_x = example_wire_x + int(0.5 * dpi)
    draw.line((wire_start_x, legend_y, wire_end_x, legend_y), fill="black", width=line_width)
    
    # Arrow at end
    arrow_angle = math.radians(25)
    left_x = wire_end_x - arrow_length * math.cos(0 - arrow_angle)
    left_y = legend_y - arrow_length * math.sin(0 - arrow_angle)
    right_x = wire_end_x - arrow_length * math.cos(0 + arrow_angle)
    right_y = legend_y - arrow_length * math.sin(0 + arrow_angle)
    draw.polygon([(wire_end_x, legend_y), (left_x, left_y), (right_x, right_y)], fill="blue")
    
    draw.text((wire_end_x + int(0.2 * dpi), legend_y), "= Wire (arrow points from End A to End B)", 
              fill="black", font=legend_font, anchor="lm")
    
    # Save image with proper DPI metadata
    img.save(output_path, dpi=(dpi, dpi))

def add_net_overlay_groups_to_svg(filepath):
    """
    Adds net overlay group markers at the end of an SVG file (before the closing </svg> tag).
    
    Args:
        filepath (str): Path to the SVG file to modify
        artifact_id (str): Identifier to use in the group IDs
    """
    with open(filepath, "r", encoding="utf-8") as file:
        svg_content = file.read()
    
    # Find the closing </svg> tag
    svg_end_match = re.search(r'</svg>\s*$', svg_content, re.DOTALL)
    
    if not svg_end_match:
        raise ValueError("Could not find closing </svg> tag")
    
    # Insert the new groups before the closing </svg> tag
    insert_position = svg_end_match.start()
    
    new_groups = (
        f'  <g id="{artifact_id}-net-overlay-contents-start">\n'
        f'  </g>\n'
        f'  <g id="{artifact_id}-net-overlay-contents-end"/>\n'
    )
    
    updated_svg_content = (
        svg_content[:insert_position] +
        new_groups +
        svg_content[insert_position:]
    )
    
    # Write back to file
    with open(filepath, "w", encoding="utf-8") as file:
        file.write(updated_svg_content)
        

# =============== MAIN MACRO LOGIC =========================================================================

schematic_path = fileio.path("kicad sch", structure_dict=file_structure())

if not os.path.isfile(schematic_path):
    raise FileNotFoundError(
        f"Schematic not found. Check your kicad sch exists at this name and location: \n{schematic_path}"
    )

# Parse the schematic
parser = KiCadSchematicParser(schematic_path)
pin_locations_of_lib_symbols, locations_of_lib_instances, wire_locations = parser.parse()

# Compile absolute pin locations
pin_locations = compile_pin_locations(pin_locations_of_lib_symbols, locations_of_lib_instances)

# Round to nearest 0.1 mil and scale to inches (keep in memory only)
pin_locations_of_lib_symbols_scaled = round_and_scale_coordinates(pin_locations_of_lib_symbols, KICAD_UNIT_SCALE)
locations_of_lib_instances_scaled = round_and_scale_coordinates(locations_of_lib_instances, KICAD_UNIT_SCALE)
wire_locations_scaled = round_and_scale_coordinates(wire_locations, KICAD_UNIT_SCALE)
pin_locations_scaled = round_and_scale_coordinates(pin_locations, KICAD_UNIT_SCALE)

# Build the graph
graph = build_graph(pin_locations_scaled, wire_locations_scaled)

# Export only the graph to JSON file
graph_path = path("graph of nodes and segments")
png_path = path("schematic visualization png")

with open(graph_path, 'w') as f:
    json.dump(graph, f, indent=2)

# Generate PNG visualization
generate_schematic_png(graph, png_path)

total_pins = sum(len(pins) for pins in pin_locations.values())
pin_nodes = sum(1 for n in graph['nodes'].keys() if not n.startswith('wirejunction-'))
junction_nodes = sum(1 for n in graph['nodes'].keys() if n.startswith('wirejunction-'))

# =============== BUILD GRAPH PATHS ========================================================================

# Open instances list and filter for the given item_type
instances = []
all_instances = fileio.read_tsv("instances list")
for instance in all_instances:
    if instance.get("item_type") == item_type:
        instances.append(instance)

# Map the instances to graph paths and assign segment_order
path_found_count = 0
for instance in instances:
    from_device_refdes = instance.get("this_net_from_device_refdes")
    from_connector_name = instance.get("this_net_from_device_connector_name")
    to_device_refdes = instance.get("this_net_to_device_refdes")
    to_connector_name = instance.get("this_net_to_device_connector_name")
    
    # Skip if missing required fields
    if not all([from_device_refdes, from_connector_name, to_device_refdes, to_connector_name]):
        print(f"Skipping {instance.get('instance_name')}: missing from/to fields")
        continue
    
    # Form node IDs (refdes.connector_name format)
    from_node_id = f"{from_device_refdes}.{from_connector_name}"
    to_node_id = f"{to_device_refdes}.{to_connector_name}"
    
    # Check if both nodes exist in graph
    if from_node_id not in graph['nodes']:
        print(f"Warning: From node '{from_node_id}' not found in graph for {instance.get('instance_name')}")
        continue
    if to_node_id not in graph['nodes']:
        print(f"Warning: To node '{to_node_id}' not found in graph for {instance.get('instance_name')}")
        continue
    
    # Find path from from_node to to_node using BFS
    path_segments = []
    path_directions = []
    
    # BFS to find path
    queue = [(from_node_id, [])]  # (current_node, path_of_segments)
    visited = {from_node_id}
    
    found_path = False
    while queue and not found_path:
        current_node, current_path = queue.pop(0)
        
        if current_node == to_node_id:
            path_segments = [seg for seg, _ in current_path]
            path_directions = [direction for _, direction in current_path]
            found_path = True
            break
        
        # Check all segments for connections
        for segment_uuid, segment_info in graph['segments'].items():
            node_a = segment_info['node_at_end_a']
            node_b = segment_info['node_at_end_b']
            
            # Check if segment connects to current node
            next_node = None
            direction = None
            
            if node_a == current_node and node_b not in visited:
                next_node = node_b
                direction = "a_to_b"
            elif node_b == current_node and node_a not in visited:
                next_node = node_a
                direction = "b_to_a"
            
            if next_node:
                visited.add(next_node)
                new_path = current_path + [(segment_uuid, direction)]
                queue.append((next_node, new_path))
    
    if found_path:
        # Store the path information in the instance
        instance['graph_path_segments'] = path_segments
        instance['graph_path_directions'] = path_directions
        instance['total_segments'] = len(path_segments)
        path_found_count += 1
    else:
        print(f"No path found for {instance.get('instance_name')}: {from_node_id} → {to_node_id}")
        instance['graph_path_segments'] = []
        instance['graph_path_directions'] = []
        instance['total_segments'] = 0

# =============== BUILD SVG OVERLAY ========================================================================

# Define segment spacing (distance between parallel wires)
segment_spacing_inches = 0.05  # Adjust as needed for visual spacing
segment_spacing_px = segment_spacing_inches * 96

# Dictionary to store points to pass through for each node/segment/instance
points_to_pass_through = {}
svg_groups = []

# Calculate entry/exit points for each instance at each node
point_count = 0
for node_id, node_coords in graph['nodes'].items():
    x_node_px = node_coords['x'] * 96
    y_node_px = node_coords['y'] * 96
    
    # Find all segments connected to this node and determine their angles
    node_segment_angles = []
    node_segments = []
    flip_sort = {}
    
    for segment_uuid, segment_info in graph['segments'].items():
        node_a = segment_info['node_at_end_a']
        node_b = segment_info['node_at_end_b']
        
        if node_a == node_id:
            # Calculate angle from this node (A) toward the other node (B)
            node_b_coords = graph['nodes'][node_b]
            dx = (node_b_coords['x'] - node_coords['x']) * 96
            dy = (node_b_coords['y'] - node_coords['y']) * 96
            angle = math.degrees(math.atan2(dy, dx))
            node_segment_angles.append(angle)
            node_segments.append(segment_uuid)
            flip_sort[segment_uuid] = False
            
        elif node_b == node_id:
            # Calculate angle from this node (B) toward the other node (A)
            node_a_coords = graph['nodes'][node_a]
            dx = (node_a_coords['x'] - node_coords['x']) * 96
            dy = (node_a_coords['y'] - node_coords['y']) * 96
            angle = math.degrees(math.atan2(dy, dx))
            node_segment_angles.append(angle)
            node_segments.append(segment_uuid)
            flip_sort[segment_uuid] = True
    
    # Count how many instances pass through this node
    components_in_node = 0
    components_seen = []
    
    for instance in instances:
        parent_name = instance.get("parent_instance") or instance.get("instance_name")
        if parent_name in components_seen:
            continue
        
        path_segments = instance.get('graph_path_segments', [])
        for seg_uuid in path_segments:
            if seg_uuid in node_segments:
                components_seen.append(parent_name)
                components_in_node += 1
                break
    
    if components_in_node == 0:
        continue
    
    # Calculate node radius based on number of components
    node_radius_inches = 0.3 + math.pow(components_in_node, 1.2) * segment_spacing_inches / 4
    node_radius_px = node_radius_inches * 96
    
    # Draw gray circle if debug mode is on
    if print_circles_and_dots:
        svg_groups.append(f'<circle cx="{x_node_px:.3f}" cy="{y_node_px:.3f}" r="{node_radius_px:.3f}" fill="gray" opacity="0.5" />')
    
    # For each segment connected to this node, calculate entry/exit points
    for seg_angle, seg_uuid in zip(node_segment_angles, node_segments):
        # Collect instances that use this segment
        instances_using_segment = []
        for instance in instances:
            if seg_uuid in instance.get('graph_path_segments', []):
                instances_using_segment.append(instance.get('instance_name'))
        
        if not instances_using_segment:
            continue
        
        # Sort alphabetically
        instances_using_segment.sort()
        
        # Flip order if segment is reversed relative to this node
        if flip_sort.get(seg_uuid):
            instances_using_segment = instances_using_segment[::-1]
        
        num_seg_components = len(instances_using_segment)
        
        # Calculate position for each instance around the node perimeter
        for idx, inst_name in enumerate(instances_using_segment, start=1):
            # Calculate offset from center of segment bundle
            center_offset_from_count_inches = (idx - (num_seg_components / 2) - 0.5) * segment_spacing_inches
            center_offset_from_count_px = center_offset_from_count_inches * 96
            
            try:
                # Calculate angular offset based on arc position
                delta_angle_from_count = math.degrees(
                    math.asin(center_offset_from_count_px / node_radius_px)
                )
            except (ValueError, ZeroDivisionError):
                delta_angle_from_count = 0
            
            # Calculate final position on circle perimeter
            final_angle = seg_angle + delta_angle_from_count
            x_circleintersect = x_node_px + node_radius_px * math.cos(math.radians(final_angle))
            y_circleintersect = y_node_px + node_radius_px * math.sin(math.radians(final_angle))
            
            # Draw red dot if debug mode is on (use unflipped coordinates)
            if print_circles_and_dots:
                svg_groups.append(f'<circle cx="{x_circleintersect:.3f}" cy="{y_circleintersect:.3f}" r="3" fill="red" />')
            
            # Store the point WITH Y FLIPPED for svg_utils.draw_styled_path()
            points_to_pass_through.setdefault(node_id, {}).setdefault(seg_uuid, {})[inst_name] = {
                'x': x_circleintersect,
                'y': -y_circleintersect  # Flip Y for the paths
            }
            point_count += 1

# === BUILD CLEANED CHAINS AND SVG ===
cleaned_chains = {}

# Get unique parent instances
unique_parents = []
for instance in instances:
    parent_name = instance.get("parent_instance") or instance.get("instance_name")
    if parent_name not in unique_parents:
        unique_parents.append(parent_name)

# Build chain for each parent instance
for parent_name in unique_parents:
    # Find all instances belonging to this parent
    parent_instances = [inst for inst in instances 
                       if (inst.get("parent_instance") or inst.get("instance_name")) == parent_name]
    
    if not parent_instances:
        continue
    
    # Use the first instance to get the path information
    first_instance = parent_instances[0]
    path_segments = first_instance.get('graph_path_segments', [])
    path_directions = first_instance.get('graph_path_directions', [])
    
    if not path_segments:
        print(f"Warning: No path segments for {parent_name}")
        continue
    
    point_chain = []
    
    # Walk through each segment in the path
    for segment_uuid, direction in zip(path_segments, path_directions):
        segment_info = graph['segments'][segment_uuid]
        node_a_id = segment_info['node_at_end_a']
        node_b_id = segment_info['node_at_end_b']
        
        # Get the instance name
        inst_name = first_instance.get('instance_name')
        
        # Calculate tangent angle for this segment
        node_a_coords = graph['nodes'][node_a_id]
        node_b_coords = graph['nodes'][node_b_id]
        dx = (node_b_coords['x'] - node_a_coords['x']) * 96
        dy = (node_b_coords['y'] - node_a_coords['y']) * 96
        tangent_ab = math.degrees(math.atan2(dy, dx))
        
        if direction == "a_to_b":
            # Get entry point at node A and exit point at node B
            if (node_a_id in points_to_pass_through and 
                segment_uuid in points_to_pass_through[node_a_id] and
                inst_name in points_to_pass_through[node_a_id][segment_uuid]):
                
                point_a = points_to_pass_through[node_a_id][segment_uuid][inst_name]
                point_chain.append({
                    'x': point_a['x'],
                    'y': point_a['y'],
                    'tangent': tangent_ab
                })
            else:
                print(f"  Missing point A for {inst_name} at {node_a_id}/{segment_uuid}")
            
            if (node_b_id in points_to_pass_through and 
                segment_uuid in points_to_pass_through[node_b_id] and
                inst_name in points_to_pass_through[node_b_id][segment_uuid]):
                
                point_b = points_to_pass_through[node_b_id][segment_uuid][inst_name]
                point_chain.append({
                    'x': point_b['x'],
                    'y': point_b['y'],
                    'tangent': tangent_ab
                })
            else:
                print(f"  Missing point B for {inst_name} at {node_b_id}/{segment_uuid}")
        
        else:  # direction == "b_to_a"
            tangent_ba = tangent_ab + 180
            if tangent_ba > 360:
                tangent_ba -= 360
            
            # Get entry point at node B and exit point at node A
            if (node_b_id in points_to_pass_through and 
                segment_uuid in points_to_pass_through[node_b_id] and
                inst_name in points_to_pass_through[node_b_id][segment_uuid]):
                
                point_b = points_to_pass_through[node_b_id][segment_uuid][inst_name]
                point_chain.append({
                    'x': point_b['x'],
                    'y': point_b['y'],
                    'tangent': tangent_ba
                })
            else:
                print(f"  Missing point B for {inst_name} at {node_b_id}/{segment_uuid}")
            
            if (node_a_id in points_to_pass_through and 
                segment_uuid in points_to_pass_through[node_a_id] and
                inst_name in points_to_pass_through[node_a_id][segment_uuid]):
                
                point_a = points_to_pass_through[node_a_id][segment_uuid][inst_name]
                point_chain.append({
                    'x': point_a['x'],
                    'y': point_a['y'],
                    'tangent': tangent_ba
                })
            else:
                print(f"  Missing point A for {inst_name} at {node_a_id}/{segment_uuid}")
    
    if point_chain:
        cleaned_chains[parent_name] = point_chain
        
        # Get appearance from instance
        appearance_data = first_instance.get('appearance', {'base_color': 'blue', 'outline_color': 'black'})
        
        # Draw the styled path
        svg_utils.draw_styled_path(
            point_chain,
            0.01,  # stroke width in inches
            appearance_data,
            svg_groups,
        )
        
    else:
        print(f"Empty chain for {parent_name}")

# === EXPORT KICAD SCHEMATIC TO SVG ===

try:
    import subprocess
    result = subprocess.run(
        ["kicad-cli", "sch", "export", "svg", "--output", dirpath(f"{artifact_id}-kicad-direct-export"), schematic_path],
        capture_output=True,
        text=True,
        check=True
    )
    
except subprocess.CalledProcessError as e:
    print(f"Error exporting KiCad schematic:")
    print(f"  stdout: {e.stdout}")
    print(f"  stderr: {e.stderr}")
except FileNotFoundError:
    print(f"kicad-cli not found. Install KiCad CLI tools.")

# Wrap the KiCad SVG contents in a group
add_net_overlay_groups_to_svg(path("kicad direct export svg"))

# === WRITE SVG OVERLAY OUTPUT ===
svg_output = (
    '<svg xmlns="http://www.w3.org/2000/svg" stroke-linecap="round" stroke-linejoin="round">\n'
    f'  <g id="{artifact_id}-net-overlay-contents-start">\n'
    + "\n".join(svg_groups)
    + "\n  </g>\n"
    f'  <g id="{artifact_id}-net-overlay-contents-end"/>\n'
    "</svg>\n"
)

overlay_svg_path = path("net overlay svg")
with open(overlay_svg_path, "w", encoding="utf-8") as f:
    f.write(svg_output)
