# import your modules here
import os
import re
import json
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

# =============== PATHS ===================================================================================
def macro_file_structure():
    return {
        f"{artifact_id}-pin-locations-lib.json": "pin locations of library symbols",
        f"{artifact_id}-instance-locations.json": "locations of library instances",
        f"{artifact_id}-wire-locations.json": "wire locations",
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

# Export to JSON files
pin_lib_path = path("pin locations of library symbols")
instance_path = path("locations of library instances")
wire_path = path("wire locations")

with open(pin_lib_path, 'w') as f:
    json.dump(pin_locations_of_lib_symbols, f, indent=2)

with open(instance_path, 'w') as f:
    json.dump(locations_of_lib_instances, f, indent=2)

with open(wire_path, 'w') as f:
    json.dump(wire_locations, f, indent=2)

print(f"Found {len(pin_locations_of_lib_symbols)} library symbols")
print(f"Found {len(locations_of_lib_instances)} symbol instances")
print(f"Found {len(wire_locations)} wires")
print(f"\nLibrary pin data saved to: {pin_lib_path}")
print(f"Instance locations saved to: {instance_path}")
print(f"Wire locations saved to: {wire_path}")