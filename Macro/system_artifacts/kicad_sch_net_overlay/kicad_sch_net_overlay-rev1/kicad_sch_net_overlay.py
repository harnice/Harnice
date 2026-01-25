# import your modules here
import os
import re
import json
import math
from typing import Dict, Set, Tuple, List
from harnice import fileio, state

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
# KiCad stores in units of 0.0254mm = 1 mil = 0.001 inches
KICAD_UNIT_SCALE = 0.001  # Convert from internal units (mils) to inches

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
            # Pattern: (pin ... (at x y angle) ... (name "pin_name"
            pin_pattern = r'\(pin\s+\w+\s+\w+\s+\(at\s+([-\d.]+)\s+([-\d.]+)\s+(\d+)\).*?\(name\s+"([^"]+)"'
            
            for pin_match in re.finditer(pin_pattern, symbol_body, re.DOTALL):
                x, y, angle, pin_name = pin_match.groups()
                
                pin_locations_of_lib_symbols[lib_id][pin_name] = {
                    'x_loc': float(x),
                    'y_loc': float(y)
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
            
            # Add the instance position to get absolute coordinates
            absolute_x = instance_x + rotated_x
            absolute_y = instance_y + rotated_y
            
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
    
    # Tolerance for considering two points as the same location (in inches)
    # Use 0.1 mils = 0.0001 inches
    TOLERANCE = 0.0001
    
    # Helper function to round coordinates for comparison
    def round_coord(value):
        return round(value / TOLERANCE) * TOLERANCE
    
    # Helper function to create a location tuple for lookup
    def location_key(x, y):
        return (round_coord(x), round_coord(y))
    
    # Map from location to node_uuid
    location_to_node = {}
    
    # Counter for junction node IDs
    junction_counter = 0
    
    # Step 1: Add all pins as nodes
    for refdes, pins in pin_locations_scaled.items():
        for pin_name, coords in pins.items():
            node_uuid = f"{refdes}.{pin_name}"  # Use dot separator
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
        
        # Create segment using wire_uuid as key
        segments[wire_uuid] = {
            'node_at_end_a': start_node,
            'node_at_end_b': end_node
        }
    
    return {
        'nodes': nodes,
        'segments': segments
    }

# =============== MAIN MACRO LOGIC =========================================================================

schematic_path = fileio.path("kicad sch", structure_dict=file_structure())

if not os.path.isfile(schematic_path):
    raise FileNotFoundError(
        f"Schematic not found. Check your kicad sch exists at this name and location: \n{schematic_path}"
    )

# Parse the schematic
print("Parsing KiCad schematic...")
parser = KiCadSchematicParser(schematic_path)
pin_locations_of_lib_symbols, locations_of_lib_instances, wire_locations = parser.parse()

# Compile absolute pin locations
print("Compiling absolute pin locations...")
pin_locations = compile_pin_locations(pin_locations_of_lib_symbols, locations_of_lib_instances)

# Round to nearest 0.1 mil and scale to inches
print(f"Rounding to nearest 0.1 mil and converting to inches...")
pin_locations_of_lib_symbols_scaled = round_and_scale_coordinates(pin_locations_of_lib_symbols, KICAD_UNIT_SCALE)
locations_of_lib_instances_scaled = round_and_scale_coordinates(locations_of_lib_instances, KICAD_UNIT_SCALE)
wire_locations_scaled = round_and_scale_coordinates(wire_locations, KICAD_UNIT_SCALE)
pin_locations_scaled = round_and_scale_coordinates(pin_locations, KICAD_UNIT_SCALE)

# Build the graph
print("Building graph of nodes and segments...")
graph = build_graph(pin_locations_scaled, wire_locations_scaled)

# Export to JSON files
pin_lib_path = path("pin locations of library symbols")
instance_path = path("locations of library instances")
wire_path = path("wire locations")
pin_path = path("absolute pin locations by refdes")
graph_path = path("graph of nodes and segments")

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

print(f"Found {len(pin_locations_of_lib_symbols)} library symbols")
print(f"Found {len(locations_of_lib_instances)} symbol instances")
print(f"Found {len(wire_locations)} wires")
total_pins = sum(len(pins) for pins in pin_locations.values())
print(f"Compiled {total_pins} absolute pin locations")
print(f"Created graph with {len(graph['nodes'])} nodes and {len(graph['segments'])} segments")
pin_nodes = sum(1 for n in graph['nodes'].keys() if not n.startswith('wirejunction-'))
junction_nodes = sum(1 for n in graph['nodes'].keys() if n.startswith('wirejunction-'))
print(f"  - Pin nodes: {pin_nodes}")
print(f"  - Junction nodes: {junction_nodes}")
print(f"\nAll coordinates rounded to nearest 0.1 mil and converted to inches")
print(f"Library pin data saved to: {pin_lib_path}")
print(f"Instance locations saved to: {instance_path}")
print(f"Wire locations saved to: {wire_path}")
print(f"Absolute pin locations saved to: {pin_path}")
print(f"Graph saved to: {graph_path}")