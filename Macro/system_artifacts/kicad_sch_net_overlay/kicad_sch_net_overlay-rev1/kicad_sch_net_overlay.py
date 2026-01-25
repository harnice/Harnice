# import your modules here
import os
import re
import json
import math
from typing import Dict
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

# =============== PATHS ===================================================================================
def macro_file_structure():
    return {
        f"{artifact_id}-pin-locations-lib.json": "pin locations of library symbols",
        f"{artifact_id}-instance-locations.json": "locations of library instances",
        f"{artifact_id}-wire-locations.json": "wire locations",
        f"{artifact_id}-pin-locations.json": "absolute pin locations by refdes",
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
    Round coordinates to nearest 0.1 mil, then scale to inches.
    Recursively processes nested dictionaries.
    """
    if isinstance(data, dict):
        processed = {}
        for key, value in data.items():
            if key in ['x_loc', 'y_loc', 'x', 'y', 'start_x', 'start_y', 'end_x', 'end_y']:
                # Round to nearest 0.1 mil (multiply by 10, round, divide by 10)
                rounded_mils = round(value * 10) / 10
                processed[key] = rounded_mils * scale_factor
            else:
                processed[key] = round_and_scale_coordinates(value, scale_factor)
        return processed
    else:
        return data

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

# Export to JSON files
pin_lib_path = path("pin locations of library symbols")
instance_path = path("locations of library instances")
wire_path = path("wire locations")
pin_path = path("absolute pin locations by refdes")

with open(pin_lib_path, 'w') as f:
    json.dump(pin_locations_of_lib_symbols_scaled, f, indent=2)

with open(instance_path, 'w') as f:
    json.dump(locations_of_lib_instances_scaled, f, indent=2)

with open(wire_path, 'w') as f:
    json.dump(wire_locations_scaled, f, indent=2)

with open(pin_path, 'w') as f:
    json.dump(pin_locations_scaled, f, indent=2)

print(f"Found {len(pin_locations_of_lib_symbols)} library symbols")
print(f"Found {len(locations_of_lib_instances)} symbol instances")
print(f"Found {len(wire_locations)} wires")
total_pins = sum(len(pins) for pins in pin_locations.values())
print(f"Compiled {total_pins} absolute pin locations")
print(f"\nAll coordinates rounded to nearest 0.1 mil and converted to inches")
print(f"Library pin data saved to: {pin_lib_path}")
print(f"Instance locations saved to: {instance_path}")
print(f"Wire locations saved to: {wire_path}")
print(f"Absolute pin locations saved to: {pin_path}")