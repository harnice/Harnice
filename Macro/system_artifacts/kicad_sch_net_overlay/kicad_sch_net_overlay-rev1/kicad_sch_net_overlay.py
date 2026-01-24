# import your modules here
import os
import subprocess
import re
import json
from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional
from harnice import fileio, state
from harnice.utils import svg_utils

# describe your args here. comment them out and do not officially define because they are called via runpy,
# for example, the caller feature_tree should define the arguments like this:
# feature_tree_utils.run_macro(
#    "kicad_sch_to_svg_no_nets",
#    "harness_artifacts",
#    "https://github.com/harnice/harnice-library-public",
#    artifact_id="kicad-schematic-svg-no-nets",
#    input_schematic="kicad/my_project.kicad_sch",
#    kicad_cli="kicad-cli",  # optional
# )
#
# Expected args (injected by caller or defaulted below):
# artifact_id: str (optional override)
# base_directory: str | None  (optional override)

# define the artifact_id of this macro (treated the same as part number). should match the filename.
artifact_id = "kicad_sch_net_overlay"

# =============== PATHS ===================================================================================
# this function does not need to be called in your macro, just by the default functions below.
# add your file structure inside here: keys are filenames, values are human-readable references. keys with contents are folder names.
def macro_file_structure():
    # define the dictionary of the file structure of this macro
    return {
        f"{artifact_id}.log.txt": "kicad-cli export log",
        f"{artifact_id}-svgs.txt": "notes about exported svgs",
        f"{artifact_id}-wire-data.json": "parsed wire routing data",
        "kicad_direct_exports": {},
        "kicad_net_overlay": {}
    }

def file_structure():
    return {
        "kicad": {
            f"{state.partnumber('pn-rev')}.kicad_sch": "kicad sch",
        }
    }


# this runs automatically and is used to assign a default base directory if it is not called by the caller.
if base_directory == None:  # path between cwd and the file structure for this macro
    base_directory = os.path.join("instance_data", "macro", artifact_id)


# call this in your script to get the path to a file in this macro. it references logic from fileio but passes in the structure from this macro.
def path(target_value):
    return fileio.path(
        target_value,
        structure_dict=macro_file_structure(),
        base_directory=base_directory,
    )


def dirpath(target_value):
    # target_value = None will return the root of this macro
    return fileio.dirpath(
        target_value,
        structure_dict=macro_file_structure(),
        base_directory=base_directory,
    )


# don't forget to make the directories you've defined above.
os.makedirs(
    dirpath("kicad_direct_exports"),
    exist_ok=True,
)
os.makedirs(
    dirpath("kicad_net_overlay"),
    exist_ok=True,
)

# =============== WIRE PARSER CLASSES ======================================================================

@dataclass
class Point:
    x: float
    y: float
    
    def __hash__(self):
        return hash((self.x, self.y))
    
    def __eq__(self, other):
        return self.x == other.x and self.y == other.y


@dataclass
class Wire:
    start: Point
    end: Point
    net: Optional[str] = None
    uuid: Optional[str] = None


@dataclass
class Junction:
    point: Point
    uuid: Optional[str] = None


@dataclass
class Pin:
    symbol_ref: str
    pin_number: str
    pin_name: str
    position: Point
    angle: int  # 0, 90, 180, 270


@dataclass
class Label:
    text: str
    position: Point


class KiCadSchematicParser:
    def __init__(self, filepath):
        with open(filepath, 'r') as f:
            self.content = f.read()
        
        self.wires = []
        self.junctions = []
        self.pins = []
        self.labels = []
        self.symbols = {}  # uuid -> symbol info
        
    def parse(self):
        """Parse all wire-related elements from the schematic"""
        self._parse_symbols()
        self._parse_wires()
        self._parse_junctions()
        self._parse_labels()
        self._parse_pins()
        
    def _parse_symbols(self):
        """Extract symbol positions and references"""
        symbol_pattern = r'\(symbol\s+\(lib_id\s+"([^"]+)"\)\s+\(at\s+([\d.]+)\s+([\d.]+)\s+(\d+)\).*?\(uuid\s+"([^"]+)"\)(.*?)\(instances'
        
        for match in re.finditer(symbol_pattern, self.content, re.DOTALL):
            lib_id, x, y, angle, uuid, symbol_body = match.groups()
            
            # Extract reference
            ref_match = re.search(r'\(property\s+"Reference"\s+"([^"]+)"', symbol_body)
            ref = ref_match.group(1) if ref_match else "?"
            
            self.symbols[uuid] = {
                'lib_id': lib_id,
                'reference': ref,
                'position': Point(float(x), float(y)),
                'angle': int(angle)
            }
    
    def _parse_wires(self):
        """Extract wire segments with their coordinates"""
        print("=" * 80)
        
        # The actual format has newlines/tabs between elements
        # (wire
        #   (pts
        #     (xy x1 y1) (xy x2 y2)
        #   )
        #   (stroke ...)
        #   (uuid "...")
        # )
        wire_pattern = r'\(wire\s+\(pts\s+\(xy\s+([\d.]+)\s+([\d.]+)\)\s+\(xy\s+([\d.]+)\s+([\d.]+)\)\s+\)[\s\S]*?\(uuid\s+"([^"]+)"\)'
        
        matches = list(re.finditer(wire_pattern, self.content))
        print(f"Wire pattern found {len(matches)} matches")
        for match in matches:
            x1, y1, x2, y2, uuid = match.groups()
            wire = Wire(
                start=Point(float(x1), float(y1)),
                end=Point(float(x2), float(y2)),
                uuid=uuid
            )
            self.wires.append(wire)
            print(f"Found wire: ({x1}, {y1}) -> ({x2}, {y2})")
        print("=" * 80)
    
    def _parse_junctions(self):
        """Extract junction points"""
        junction_pattern = r'\(junction\s+\(at\s+([\d.]+)\s+([\d.]+)\).*?\(uuid\s+"([^"]+)"\)'
        
        for match in re.finditer(junction_pattern, self.content, re.DOTALL):
            x, y, uuid = match.groups()
            junction = Junction(
                point=Point(float(x), float(y)),
                uuid=uuid
            )
            self.junctions.append(junction)
    
    def _parse_labels(self):
        """Extract net labels"""
        # Updated pattern to handle the actual format with effects block
        label_pattern = r'\(label\s+"([^"]+)"\s+\(at\s+([\d.]+)\s+([\d.]+)\s+[\d.]+\)'
        
        print("=" * 80)
        for match in re.finditer(label_pattern, self.content):
            text, x, y = match.groups()
            label = Label(
                text=text,
                position=Point(float(x), float(y))
            )
            self.labels.append(label)
            print(f"Found label: '{text}' at ({x}, {y})")
        print("=" * 80)
    
    def _parse_pins(self):
        """Extract pin locations from symbol definitions and instances"""
        # This is simplified - you'd need to match pin definitions with symbol instances
        # and calculate actual pin positions based on symbol position + rotation
        
        # For now, we'll extract from the netlist or infer from wire endpoints
        pass
    
    def find_net_for_wire(self, wire: Wire) -> Optional[str]:
        """Find which net a wire belongs to by checking nearby labels"""
        # Simple heuristic: find the closest label
        min_dist = float('inf')
        closest_label = None
        
        wire_midpoint = Point(
            (wire.start.x + wire.end.x) / 2,
            (wire.start.y + wire.end.y) / 2
        )
        
        for label in self.labels:
            dist = ((label.position.x - wire_midpoint.x)**2 + 
                   (label.position.y - wire_midpoint.y)**2)**0.5
            if dist < min_dist:
                min_dist = dist
                closest_label = label.text
        
        # Also check if wire endpoints match junction points
        return closest_label
    
    def get_wire_network(self) -> Dict[str, List[Dict]]:
        """
        Group wires by net and return routing information
        Returns dict with net names as keys and wire info as values
        """
        # Build a connectivity map
        point_to_wires = {}
        
        for wire in self.wires:
            for pt in [wire.start, wire.end]:
                if pt not in point_to_wires:
                    point_to_wires[pt] = []
                point_to_wires[pt].append(wire)
        
        # Assign nets to wires by propagation
        wire_nets = {}
        for label in self.labels:
            # Find wires near this label
            for wire in self.wires:
                # Check if label is on or very near the wire
                if self._point_near_wire(label.position, wire):
                    wire_nets[wire.uuid] = label.text
        
        # Propagate net names through connected wires
        changed = True
        while changed:
            changed = False
            for pt, wires_at_pt in point_to_wires.items():
                net_names = [wire_nets.get(w.uuid) for w in wires_at_pt if w.uuid in wire_nets]
                if net_names:
                    net_name = net_names[0]
                    for w in wires_at_pt:
                        if w.uuid not in wire_nets:
                            wire_nets[w.uuid] = net_name
                            changed = True
        
        # Group by net
        nets = {}
        for wire in self.wires:
            net = wire_nets.get(wire.uuid, "unassigned")
            if net not in nets:
                nets[net] = []
            
            nets[net].append({
                'start': {'x': wire.start.x, 'y': wire.start.y},
                'end': {'x': wire.end.x, 'y': wire.end.y},
                'uuid': wire.uuid
            })
        
        return nets
    
    def _point_near_wire(self, point: Point, wire: Wire, threshold: float = 5.0) -> bool:
        """Check if a point is near a wire segment"""
        # Calculate distance from point to line segment
        x0, y0 = point.x, point.y
        x1, y1 = wire.start.x, wire.start.y
        x2, y2 = wire.end.x, wire.end.y
        
        # Vector from start to end
        dx, dy = x2 - x1, y2 - y1
        
        if dx == 0 and dy == 0:
            # Degenerate case
            return ((x0 - x1)**2 + (y0 - y1)**2)**0.5 < threshold
        
        # Parameter t for the projection of point onto line
        t = max(0, min(1, ((x0 - x1) * dx + (y0 - y1) * dy) / (dx*dx + dy*dy)))
        
        # Closest point on segment
        closest_x = x1 + t * dx
        closest_y = y1 + t * dy
        
        # Distance to closest point
        dist = ((x0 - closest_x)**2 + (y0 - closest_y)**2)**0.5
        
        return dist < threshold
    
    def export_json(self, output_path: str):
        """Export parsed data to JSON"""
        data = {
            'nets': self.get_wire_network(),
            'junctions': [
                {
                    'x': j.point.x,
                    'y': j.point.y,
                    'uuid': j.uuid
                }
                for j in self.junctions
            ],
            'labels': [
                {
                    'text': l.text,
                    'x': l.position.x,
                    'y': l.position.y
                }
                for l in self.labels
            ],
            'symbols': {
                uuid: {
                    'reference': info['reference'],
                    'lib_id': info['lib_id'],
                    'x': info['position'].x,
                    'y': info['position'].y,
                    'angle': info['angle']
                }
                for uuid, info in self.symbols.items()
            }
        }
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        return data

# =============== MAIN MACRO LOGIC =========================================================================
# macro initialization complete. write the rest of the macro logic here.
# ==========================================================================================================

schematic_path = fileio.path("kicad sch", structure_dict=file_structure())

if not os.path.isfile(schematic_path):
    raise FileNotFoundError(
        f"Schematic not found. Check your kicad sch exists at this name and location: \n{schematic_path}"
    )

cmd = [
    "kicad-cli",
    "sch",
    "export",
    "svg",
    schematic_path,
    "-o",
    dirpath("kicad_direct_exports"),
]

subprocess.run(cmd, check=True, capture_output=True)

# Parse the schematic to extract wire routing data
print("Parsing schematic for wire routing data...")
parser = KiCadSchematicParser(schematic_path)
parser.parse()

# Export wire data to JSON for reference
wire_data_path = path("parsed wire routing data")
wire_data = parser.export_json(wire_data_path)

print(f"Found {len(parser.wires)} wire segments")
print(f"Found {len(parser.junctions)} junctions")
print(f"Found {len(parser.labels)} labels")
print(f"Nets found:")
for net_name, wires in wire_data['nets'].items():
    print(f"  {net_name}: {len(wires)} segments")

for svg in os.listdir(dirpath("kicad_direct_exports")):
    docname = svg.replace('.svg', '')
    direct_export_path = os.path.join(dirpath("kicad_direct_exports"), svg)
    overlay_path = os.path.join(dirpath("kicad_net_overlay"), f"{docname}-overlay.svg")
    svg_utils.add_entire_svg_file_contents_to_group(direct_export_path, f"{docname}-kicad_direct_export")
    
    net_overlay_path = os.path.join(dirpath("kicad_net_overlay"), svg)

    if not os.path.isfile(net_overlay_path):
        with open(net_overlay_path, "w") as f:
            f.write(f"""<svg xmlns="http://www.w3.org/2000/svg" version="1.1">
<g id="{docname}-kicad_direct_export-contents-start">
</g>
<g id="{docname}-kicad_direct_export-contents-end">
</g>
</svg>""")

    svg_utils.find_and_replace_svg_group(
        direct_export_path,
        f"{docname}-kicad_direct_export",
        net_overlay_path,
        f"{docname}-kicad_direct_export",
    )