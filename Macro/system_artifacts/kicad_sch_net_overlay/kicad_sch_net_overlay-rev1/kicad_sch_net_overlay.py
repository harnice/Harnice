# import your modules here
import os
import re
import json
import math
from typing import Dict, Set, Tuple, List
from harnice import fileio, state
from PIL import Image, ImageDraw, ImageFont

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

# define the artifact_id of this macro (treated the same as part number). should match the filename.
artifact_id = "kicad_sch_parser"

# KiCad internal units to inches conversion
# KiCad v6+ schematics store coordinates in millimeters
# Need to convert mm to inches: 1 inch = 25.4 mm
KICAD_UNIT_SCALE = 1.0 / 25.4  # Convert from millimeters to inches

# Precision for final output (number of decimal places)
OUTPUT_PRECISION = 5

# =============== PATHS ===================================================================================
def macro_file_structure():
    return {
        f"{artifact_id}-pin-locations-lib.json": "pin locations of library symbols",
        f"{artifact_id}-instance-locations.json": "locations of library instances",
        f"{artifact_id}-wire-locations.json": "wire locations",
        f"{artifact_id}-pin-locations.json": "absolute pin locations by refdes",
        f"{artifact_id}-graph.json": "graph of nodes and segments",
        f"{artifact_id}-schematic-visualization.png": "schematic visualization png",
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
                'start_x': xxxx,
                'start_y': xxxx,
                'end_x': xxxx,
                'end_y': xxxx
            }
        }
        """
        wire_locations = {}
        
        # Pattern: (wire (pts (xy x1 y1) (xy x2 y2)) ... (uuid "...")
        wire_pattern = r'\(wire\s+\(pts\s+\(xy\s+([-\d.]+)\s+([-\d.]+)\)\s+\(xy\s+([-\d.]+)\s+([-\d.]+)\)\s+\)[\s\S]*?\(uuid\s+"([^"]+)"\)'
        
        for match in re.finditer(wire_pattern, self.content):
            x1, y1, x2, y2, uuid = match.groups()
            
            wire_locations[uuid] = {
                'start_x': float(x1),
                'start_y': float(y1),
                'end_x': float(x2),
                'end_y': float(y2)
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
            if key in ['x_loc', 'y_loc', 'x', 'y', 'start_x', 'start_y', 'end_x', 'end_y']:
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
        start_x = wire_coords['start_x']
        start_y = wire_coords['start_y']
        end_x = wire_coords['end_x']
        end_y = wire_coords['end_y']
        
        start_key = location_key(start_x, start_y)
        end_key = location_key(end_x, end_y)
        
        # Get or create node for start point
        if start_key not in location_to_node:
            junction_uuid = f"wirejunction-{junction_counter}"
            junction_counter += 1
            nodes[junction_uuid] = {
                'x': round(start_x, OUTPUT_PRECISION),
                'y': round(start_y, OUTPUT_PRECISION)
            }
            location_to_node[start_key] = junction_uuid
        
        start_node = location_to_node[start_key]
        
        # Get or create node for end point
        if end_key not in location_to_node:
            junction_uuid = f"wirejunction-{junction_counter}"
            junction_counter += 1
            nodes[junction_uuid] = {
                'x': round(end_x, OUTPUT_PRECISION),
                'y': round(end_y, OUTPUT_PRECISION)
            }
            location_to_node[end_key] = junction_uuid
        
        end_node = location_to_node[end_key]
        
        segments[wire_uuid] = {
            'node_at_end_a': start_node,
            'node_at_end_b': end_node
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
    arrow_length_inches = 0.067  # 1/3 of 0.2in
    line_width_inches = 0.02
    
    # Convert to pixels
    pin_radius = int(pin_radius_inches * dpi)
    junction_radius = int(junction_radius_inches * dpi)
    font_size = int(font_size_inches * dpi)
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
        legend_font = ImageFont.truetype("Arial.ttf", font_size)
    except OSError:
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
            legend_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
        except OSError:
            font = ImageFont.load_default()
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
        
        # Label all nodes with their names
        label_offset = int(0.15 * dpi)  # 0.15 inch above the node
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

# Round to nearest 0.1 mil and scale to inches
pin_locations_of_lib_symbols_scaled = round_and_scale_coordinates(pin_locations_of_lib_symbols, KICAD_UNIT_SCALE)
locations_of_lib_instances_scaled = round_and_scale_coordinates(locations_of_lib_instances, KICAD_UNIT_SCALE)
wire_locations_scaled = round_and_scale_coordinates(wire_locations, KICAD_UNIT_SCALE)
pin_locations_scaled = round_and_scale_coordinates(pin_locations, KICAD_UNIT_SCALE)

# Build the graph
graph = build_graph(pin_locations_scaled, wire_locations_scaled)

# Export to JSON files
pin_lib_path = path("pin locations of library symbols")
instance_path = path("locations of library instances")
wire_path = path("wire locations")
pin_path = path("absolute pin locations by refdes")
graph_path = path("graph of nodes and segments")
png_path = path("schematic visualization png")

with open(pin_lib_path, 'w') as f:
    json.dump(pin_locations_of_lib_symbols_scaled, f, indent=2)

with open(instance_path, 'w') as f:
    json.dump(locations_of_lib_instances_scaled, f, indent=2)

with open(wire_path, 'w') as f:
    json.dump(wire_locations_scaled, f, indent=2)

with open(pin_path, 'w') as f:
    json.dump(pin_locations_scaled, f, indent=2)

with open(graph_path, 'w') as f:
    json.dump(graph, f, indent=2)

# Generate PNG visualization
generate_schematic_png(graph, png_path)

total_pins = sum(len(pins) for pins in pin_locations.values())
pin_nodes = sum(1 for n in graph['nodes'].keys() if not n.startswith('wirejunction-'))
junction_nodes = sum(1 for n in graph['nodes'].keys() if n.startswith('wirejunction-'))