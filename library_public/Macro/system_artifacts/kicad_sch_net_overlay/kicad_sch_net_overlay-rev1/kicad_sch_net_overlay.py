# import your modules here
import os
import re
import json
import math
from typing import Dict, List
from harnice import fileio, state
from PIL import Image, ImageDraw, ImageFont
from harnice.utils import svg_utils

# Expected args (injected by caller or defaulted below):
# artifact_id: str (optional override)
# base_directory: str | None  (optional override)
# instances: list of instances to plot

# define the artifact_id of this macro (treated the same as part number). should match the filename.
artifact_id = "kicad_sch_parser"

# KiCad internal units to inches conversion
# KiCad v6+ schematics store coordinates in millimeters
# Need to convert mm to inches: 1 inch = 25.4 mm
KICAD_UNIT_SCALE = 1.0 / 25.4  # Convert from millimeters to inches

# Precision for final output (number of decimal places)
OUTPUT_PRECISION = 5

# Scale factor for labels (1.0 since coordinates are already in mm for SVG)
scale = 1.0

# Minimum segment length (in mm) to show white labels
MIN_SEGMENT_LENGTH_FOR_LABEL_MM = 30.0

print_circles_and_dots = False  # for debugging the path

"""
Known issues:

- Multiple pages of kicad schematic are not supported
- Multi-circuit junctions are not supported
- Kicad buses are not supported
"""


# =============== PATHS ===================================================================================
def macro_file_structure():
    return {
        f"{artifact_id}-graph.json": "graph of nodes and segments",
        f"{artifact_id}-schematic-visualization.png": "schematic visualization png",
        f"{artifact_id}-kicad-direct-export": {  # i think this is because kicad exports svgs into a directory with the same name as the target file
            f"{state.partnumber('pn')}-{state.partnumber('rev')}.svg": "kicad direct export svg",
        },
        "overlay_svgs": {
            f"{artifact_id}-net-overlay.svg": "net overlay svg",
        },
        f"{state.partnumber('pn-rev')}-{item_type}_block_diagram.pdf": "output pdf",
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
        with open(filepath, "r") as f:
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
        lib_symbols_match = re.search(
            r"\(lib_symbols(.*?)\n\t\)", self.content, re.DOTALL
        )
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
                    "x_loc": x,
                    "y_loc": y,
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
                "x": float(x),
                "y": float(y),
                "rotate": float(rotate),
                "lib_id": lib_id,
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
                "a_x": float(x1),
                "a_y": float(y1),
                "b_x": float(x2),
                "b_y": float(y2),
            }

        return wire_locations

    def _parse_labels(self) -> List[Dict]:
        """
        Parse text labels and net labels from the schematic.
        Returns:
        [
            {
                'text': '...',
                'x': xxxx,
                'y': xxxx,
                'angle': xxxx,
                'type': 'text' or 'label'
            },
            ...
        ]
        """
        labels = []

        # Pattern for text labels: (text "..." (at x y angle) ...)
        text_pattern = r'\(text\s+"([^"]+)"\s+\(at\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\)'
        
        for match in re.finditer(text_pattern, self.content):
            text, x, y, angle = match.groups()
            labels.append({
                'text': text,
                'x': float(x),
                'y': float(y),
                'angle': float(angle),
                'type': 'text'
            })

        # Pattern for net labels: (label "..." (at x y angle) ...)
        label_pattern = r'\(label\s+"([^"]+)"\s+\(at\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\)'
        
        for match in re.finditer(label_pattern, self.content):
            text, x, y, angle = match.groups()
            labels.append({
                'text': text,
                'x': float(x),
                'y': float(y),
                'angle': float(angle),
                'type': 'label'
            })

        return labels


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
        lib_id = instance_info["lib_id"]
        instance_x = instance_info["x"]
        instance_y = instance_info["y"]
        instance_rotate = instance_info["rotate"]

        # Check if we have pin data for this lib_id
        if lib_id not in pin_locations_of_lib_symbols:
            print(
                f"Warning: No pin data found for lib_id '{lib_id}' (used by {refdes})"
            )
            continue

        pin_locations[refdes] = {}

        # For each pin in the library symbol, calculate its absolute position
        for pin_name, pin_info in pin_locations_of_lib_symbols[lib_id].items():
            pin_x_rel = pin_info["x_loc"]
            pin_y_rel = pin_info["y_loc"]

            # Rotate the pin relative position by the instance rotation
            rotated_x, rotated_y = rotate_point(pin_x_rel, pin_y_rel, instance_rotate)

            # KiCad Y coordinate is inverted in symbol definitions
            # Y increases downward in schematic, but symbol coords use upward Y
            absolute_x = instance_x + rotated_x
            absolute_y = instance_y - rotated_y  # SUBTRACT Y

            pin_locations[refdes][pin_name] = {"x_loc": absolute_x, "y_loc": absolute_y}

    return pin_locations


def round_and_scale_coordinates(data, scale_factor):
    """
    Round coordinates to nearest 0.1 mil, then scale to inches, then round to output precision.
    Recursively processes nested dictionaries.
    """
    if isinstance(data, dict):
        processed = {}
        for key, value in data.items():
            if key in ["x_loc", "y_loc", "x", "y", "a_x", "a_y", "b_x", "b_y"]:
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
            x = coords["x_loc"]
            y = coords["y_loc"]

            nodes[node_uuid] = {
                "x": round(x, OUTPUT_PRECISION),
                "y": round(y, OUTPUT_PRECISION),
            }

            loc_key = location_key(x, y)
            location_to_node[loc_key] = node_uuid

    # Step 2: Process wires and create junction nodes where needed
    for wire_uuid, wire_coords in wire_locations_scaled.items():
        a_x = wire_coords["a_x"]
        a_y = wire_coords["a_y"]
        b_x = wire_coords["b_x"]
        b_y = wire_coords["b_y"]

        a_key = location_key(a_x, a_y)
        b_key = location_key(b_x, b_y)

        # Get or create node for end A
        if a_key not in location_to_node:
            junction_uuid = f"wirejunction-{junction_counter}"
            junction_counter += 1
            nodes[junction_uuid] = {
                "x": round(a_x, OUTPUT_PRECISION),
                "y": round(a_y, OUTPUT_PRECISION),
            }
            location_to_node[a_key] = junction_uuid

        a_node = location_to_node[a_key]

        # Get or create node for end B
        if b_key not in location_to_node:
            junction_uuid = f"wirejunction-{junction_counter}"
            junction_counter += 1
            nodes[junction_uuid] = {
                "x": round(b_x, OUTPUT_PRECISION),
                "y": round(b_y, OUTPUT_PRECISION),
            }
            location_to_node[b_key] = junction_uuid

        b_node = location_to_node[b_key]

        segments[wire_uuid] = {"node_at_end_a": a_node, "node_at_end_b": b_node}

    return {"nodes": nodes, "segments": segments}


def generate_schematic_png(graph, output_path):
    """
    Generate a PNG visualization of the schematic graph.

    Args:
        graph: Dictionary with 'nodes' and 'segments'
        output_path: Path to save the PNG file
    """
    nodes = graph["nodes"]
    segments = graph["segments"]

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
    font_size_inches = 0.05  # 1/3 of 0.15in
    wire_font_size_inches = 0.05 / 3  # 1/3 of node font size
    arrow_length_inches = 0.067  # 1/3 of 0.2in
    line_width_inches = 0.02

    # Convert to pixels
    pin_radius = int(pin_radius_inches * dpi)
    font_size = int(font_size_inches * dpi)
    wire_font_size = int(wire_font_size_inches * dpi)
    arrow_length = int(arrow_length_inches * dpi)
    line_width = max(1, int(line_width_inches * dpi))

    margin_inches = 0.5  # Margin from sheet edge
    margin_pixels = int(margin_inches * dpi)

    # Extract node coordinates (already in inches from the parser)
    node_coordinates = {name: (info["x"], info["y"]) for name, info in nodes.items()}

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
            font = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size
            )
            wire_font = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", wire_font_size
            )
            legend_font = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size
            )
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
            draw.text(
                (center_x, center_y - wire_label_offset),
                wire_uuid,
                fill="blue",
                font=wire_font,
                anchor="mm",
            )

    # --- Draw nodes ---
    for name, (x, y) in node_coordinates.items():
        cx, cy = map_xy(x, y)

        # Draw all nodes as identical circles (same style for pins and junctions)
        draw.ellipse(
            (cx - pin_radius, cy - pin_radius, cx + pin_radius, cy + pin_radius),
            fill="red",
            outline="darkred",
            width=line_width,
        )

        # Label all nodes with their names (closer to the node)
        label_offset = int(
            0.075 * dpi
        )  # 0.075 inch above the node (half of previous distance)
        draw.text((cx, cy - label_offset), name, fill="black", font=font, anchor="mm")

    # Add legend at the bottom of the sheet with visual examples
    legend_y = height - int(0.4 * dpi)  # 0.4 inches from bottom
    legend_x = margin_pixels

    # Draw example node (circle - used for all nodes)
    example_node_x = legend_x + int(0.15 * dpi)
    draw.ellipse(
        (
            example_node_x - pin_radius,
            legend_y - pin_radius,
            example_node_x + pin_radius,
            legend_y + pin_radius,
        ),
        fill="red",
        outline="darkred",
        width=line_width,
    )
    draw.text(
        (example_node_x + int(0.2 * dpi), legend_y),
        "= Node (identified by label)",
        fill="black",
        font=legend_font,
        anchor="lm",
    )

    # Draw example wire with arrow
    example_wire_x = legend_x + int(3.5 * dpi)
    wire_start_x = example_wire_x
    wire_end_x = example_wire_x + int(0.5 * dpi)
    draw.line(
        (wire_start_x, legend_y, wire_end_x, legend_y), fill="black", width=line_width
    )

    # Arrow at end
    arrow_angle = math.radians(25)
    left_x = wire_end_x - arrow_length * math.cos(0 - arrow_angle)
    left_y = legend_y - arrow_length * math.sin(0 - arrow_angle)
    right_x = wire_end_x - arrow_length * math.cos(0 + arrow_angle)
    right_y = legend_y - arrow_length * math.sin(0 + arrow_angle)
    draw.polygon(
        [(wire_end_x, legend_y), (left_x, left_y), (right_x, right_y)], fill="blue"
    )

    draw.text(
        (wire_end_x + int(0.2 * dpi), legend_y),
        "= Wire (arrow points from End A to End B)",
        fill="black",
        font=legend_font,
        anchor="lm",
    )

    # Save image with proper DPI metadata
    img.save(output_path, dpi=(dpi, dpi))


def extract_svg_viewbox(filepath):
    """
    Extracts viewBox, width, and height attributes from an SVG file.

    Args:
        filepath (str): Path to the SVG file to read

    Returns:
        dict: Dictionary with 'viewBox', 'width', and 'height' keys (values may be None)
    """
    with open(filepath, "r", encoding="utf-8") as file:
        svg_content = file.read()

    # Find the opening <svg> tag
    svg_tag_match = re.search(r"<svg[^>]*>", svg_content, re.DOTALL)
    if not svg_tag_match:
        return {"viewBox": None, "width": None, "height": None}

    svg_tag = svg_tag_match.group(0)

    # Extract viewBox
    viewbox_match = re.search(r'viewBox\s*=\s*["\']([^"\']+)["\']', svg_tag)
    viewbox = viewbox_match.group(1) if viewbox_match else None

    # Extract width
    width_match = re.search(r'width\s*=\s*["\']([^"\']+)["\']', svg_tag)
    width = width_match.group(1) if width_match else None

    # Extract height
    height_match = re.search(r'height\s*=\s*["\']([^"\']+)["\']', svg_tag)
    height = height_match.group(1) if height_match else None

    return {"viewBox": viewbox, "width": width, "height": height}


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
    svg_end_match = re.search(r"</svg>\s*$", svg_content, re.DOTALL)

    if not svg_end_match:
        raise ValueError("Could not find closing </svg> tag")

    # Insert the new groups before the closing </svg> tag
    insert_position = svg_end_match.start()

    new_groups = (
        f'  <g id="{artifact_id}-net-overlay-contents-start">\n'
        f"  </g>\n"
        f'  <g id="{artifact_id}-net-overlay-contents-end"/>\n'
    )

    updated_svg_content = (
        svg_content[:insert_position] + new_groups + svg_content[insert_position:]
    )

    # Write back to file
    with open(filepath, "w", encoding="utf-8") as file:
        file.write(updated_svg_content)


def label_svg(
    x,
    y,
    angle,
    text,
    text_color="black",
    background_color="white",
    outline="black",
    font_size=0.2,
    font_family="Arial, Helvetica, sans-serif",
    font_weight="normal",
):
    """
    Generate SVG label with text in a rectangular box.
    
    Units: All parameters and calculations are in millimeters (mm).
    - x, y: Position coordinates in mm (SVG coordinate system, Y increases downward)
    - angle: Rotation angle in degrees (tangent angle of wire segment)
    - font_size: Font size in mm (default 0.2mm)
    - All dimensions (width, height, padding, stroke) are in mm
    
    Args:
        x: X coordinate in mm
        y: Y coordinate in mm (KiCad coordinates, will be flipped for SVG)
        angle: Rotation angle in degrees (wire tangent direction)
        text: Text content to display
        text_color: Text fill color
        background_color: Box fill color ("white" or "black")
        outline: Box stroke color
        font_size: Font size in mm (default 0.2mm)
        font_family: Font family name
        font_weight: Font weight
    
    Returns:
        SVG string for the label group
    """
    # Ensure text is not None or empty - use placeholder if needed
    text_str = str(text) if text is not None else ""
    if not text_str.strip():
        text_str = "?"
    
    # Escape XML/SVG special characters in text
    text_escaped = (
        text_str
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )
    
    # All units are in millimeters (mm)
    # x, y coordinates are already in mm from point_chain (converted from inches earlier)
    # font_size parameter is in mm
    font_size_mm = font_size  # Explicitly named for clarity, but same value
    
    # Flip Y coordinate for SVG (KiCad Y increases downward, SVG Y increases upward)
    y_svg = -y
    
    # Normalize angle to 0-360 range
    angle = angle % 360
    if angle < 0:
        angle += 360
    
    # The tangent angle represents the direction of the wire segment
    # For SVG, we want text parallel to the wire direction
    # SVG rotate() is counter-clockwise, and Y increases downward
    # The tangent angle already accounts for flipped Y coordinates
    # We just need to ensure text is readable (not upside down)
    # If angle is between 90 and 270, flip it 180 degrees for readability
    if 90 < angle < 270:
        angle += 180
        angle = angle % 360

    # Calculate box dimensions (all in mm)
    # Character width: each character takes 1.2x the font size in width
    char_width_mm = font_size_mm * 1.2
    text_width_mm = len(text_escaped) * char_width_mm
    
    # Horizontal padding (left/right) in mm
    horizontal_padding_mm = 0.3
    # Box width: text width + padding, then multiplied by 1.75 for extra width
    width_mm = (text_width_mm + horizontal_padding_mm * 2) * 1.75
    
    # Box height: 4x the font size (provides vertical padding around text)
    # Text size remains font_size_mm, box is taller for better visibility
    height_mm = font_size_mm * 4
    
    # Center the rectangle around the origin (for rotation)
    rect_x_mm = -width_mm / 2
    rect_y_mm = -height_mm / 2
    
    # Stroke settings (all in mm)
    # White labels: thin border (0.05mm) for subtle outline
    # Black labels: stroke matches background (invisible, but set for consistency)
    stroke_color = outline if background_color != "black" else background_color
    if background_color == "white":
        stroke_width_mm = 0.05  # 0.25 * 0.2mm = 0.05mm for white labels
    else:
        stroke_width_mm = 0.2  # Black boxes - stroke matches background so not visible

    # Layout notes:
    # - Rectangle is centered at origin: extends from -width/2 to +width/2 (x) and -height/2 to +height/2 (y)
    # - Text is positioned at (0, 0) with dominant-baseline:middle, so it's vertically centered
    # - Font-size in SVG is font_size_mm (text size), box height is height_mm (4x text size)
    # Generate SVG (all values in mm)
    return f"""
<g transform="translate({x:.3f},{y_svg:.3f}) rotate({-angle:.3f})">
  <rect x="{rect_x_mm:.3f}" y="{rect_y_mm:.3f}"
        width="{width_mm:.3f}" height="{height_mm:.3f}"
        fill="{background_color}" stroke="{stroke_color}" stroke-width="{stroke_width_mm}"/>
  <text x="0" y="0" text-anchor="middle"
        style="fill:{text_color};dominant-baseline:middle;
               font-weight:{font_weight};font-family:{font_family};
               font-size:{font_size_mm}mm">{text_escaped}</text>
</g>
""".strip()


# =============== MAIN MACRO LOGIC =========================================================================

schematic_path = fileio.path("kicad sch", structure_dict=file_structure())

if not os.path.isfile(schematic_path):
    raise FileNotFoundError(
        f"Schematic not found. Check your kicad sch exists at this name and location: \n{schematic_path}"
    )

# Parse the schematic
parser = KiCadSchematicParser(schematic_path)
pin_locations_of_lib_symbols, locations_of_lib_instances, wire_locations = (
    parser.parse()
)

# Compile absolute pin locations
pin_locations = compile_pin_locations(
    pin_locations_of_lib_symbols, locations_of_lib_instances
)

# Round to nearest 0.1 mil and scale to inches (keep in memory only)
pin_locations_of_lib_symbols_scaled = round_and_scale_coordinates(
    pin_locations_of_lib_symbols, KICAD_UNIT_SCALE
)
locations_of_lib_instances_scaled = round_and_scale_coordinates(
    locations_of_lib_instances, KICAD_UNIT_SCALE
)
wire_locations_scaled = round_and_scale_coordinates(wire_locations, KICAD_UNIT_SCALE)
pin_locations_scaled = round_and_scale_coordinates(pin_locations, KICAD_UNIT_SCALE)

# Build the graph
graph = build_graph(pin_locations_scaled, wire_locations_scaled)

# Export only the graph to JSON file
graph_path = path("graph of nodes and segments")
png_path = path("schematic visualization png")

with open(graph_path, "w") as f:
    json.dump(graph, f, indent=2)

# Generate PNG visualization
generate_schematic_png(graph, png_path)

total_pins = sum(len(pins) for pins in pin_locations.values())
pin_nodes = sum(1 for n in graph["nodes"].keys() if not n.startswith("wirejunction-"))
junction_nodes = sum(1 for n in graph["nodes"].keys() if n.startswith("wirejunction-"))

# =============== BUILD GRAPH PATHS ========================================================================


# Map the instances to graph paths and assign segment_order
path_found_count = 0
for instance in instances: # input arg
    from_device_refdes = instance.get("this_net_from_device_refdes")
    from_connector_name = instance.get("this_net_from_device_connector_name")
    to_device_refdes = instance.get("this_net_to_device_refdes")
    to_connector_name = instance.get("this_net_to_device_connector_name")

    # Form node IDs (refdes.connector_name format)
    from_node_id = f"{from_device_refdes}.{from_connector_name}"
    to_node_id = f"{to_device_refdes}.{to_connector_name}"

    # Check if both nodes exist in graph
    if from_node_id not in graph["nodes"]:
        raise ValueError(
            f"From node '{from_node_id}' not found in graph for {instance.get('instance_name')}"
        )
    if to_node_id not in graph["nodes"]:
        raise ValueError(
            f"To node '{to_node_id}' not found in graph for {instance.get('instance_name')}"
        )

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
        for segment_uuid, segment_info in graph["segments"].items():
            node_a = segment_info["node_at_end_a"]
            node_b = segment_info["node_at_end_b"]

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
        instance["graph_path_segments"] = path_segments
        instance["graph_path_directions"] = path_directions
        instance["total_segments"] = len(path_segments)
        path_found_count += 1
    else:
        raise ValueError(
            f"No path found for {instance.get('instance_name')}: {from_node_id} → {to_node_id}"
        )

# =============== BUILD SVG OVERLAY ========================================================================

# Define segment spacing (distance between parallel wires)
segment_spacing_inches = 0.05  # Adjust as needed for visual spacing
segment_spacing_mm = (
    segment_spacing_inches * 25.4
)  # Convert to mm to match KiCad SVG coordinate system

# Dictionary to store points to pass through for each node/segment/instance
points_to_pass_through = {}
svg_groups = []

# Calculate entry/exit points for each instance at each node
point_count = 0
for node_id, node_coords in graph["nodes"].items():
    # Convert from inches to millimeters to match KiCad SVG coordinate system
    x_node_mm = node_coords["x"] * 25.4
    y_node_mm = node_coords["y"] * 25.4

    # Find all segments connected to this node and determine their angles
    node_segment_angles = []
    node_segments = []
    flip_sort = {}

    for segment_uuid, segment_info in graph["segments"].items():
        node_a = segment_info["node_at_end_a"]
        node_b = segment_info["node_at_end_b"]

        if node_a == node_id:
            # Calculate angle from this node (A) toward the other node (B)
            node_b_coords = graph["nodes"][node_b]
            # Convert from inches to millimeters to match KiCad SVG coordinate system
            dx = (node_b_coords["x"] - node_coords["x"]) * 25.4
            dy = (node_b_coords["y"] - node_coords["y"]) * 25.4
            angle = math.degrees(math.atan2(dy, dx))
            node_segment_angles.append(angle)
            node_segments.append(segment_uuid)
            flip_sort[segment_uuid] = False

        elif node_b == node_id:
            # Calculate angle from this node (B) toward the other node (A)
            node_a_coords = graph["nodes"][node_a]
            # Convert from inches to millimeters to match KiCad SVG coordinate system
            dx = (node_a_coords["x"] - node_coords["x"]) * 25.4
            dy = (node_a_coords["y"] - node_coords["y"]) * 25.4
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

        path_segments = instance.get("graph_path_segments", [])
        for seg_uuid in path_segments:
            if seg_uuid in node_segments:
                components_seen.append(parent_name)
                components_in_node += 1
                break

    if components_in_node == 0:
        continue

    # Calculate node radius based on number of components
    node_radius_inches = math.pow(components_in_node, 0.7) * segment_spacing_inches
    node_radius_mm = (
        node_radius_inches * 25.4
    )  # Convert to mm to match KiCad SVG coordinate system

    # Draw gray circle if debug mode is on
    if print_circles_and_dots:
        svg_groups.append(
            f'<circle cx="{x_node_mm:.3f}" cy="{y_node_mm:.3f}" r="{node_radius_mm:.3f}" fill="gray" opacity="0.5" />'
        )

    # For each segment connected to this node, calculate entry/exit points
    for seg_angle, seg_uuid in zip(node_segment_angles, node_segments):
        # Collect instances that use this segment
        instances_using_segment = []
        for instance in instances:
            if seg_uuid in instance.get("graph_path_segments", []):
                instances_using_segment.append(instance.get("instance_name"))

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
            center_offset_from_count_inches = (
                idx - (num_seg_components / 2) - 0.5
            ) * segment_spacing_inches
            center_offset_from_count_mm = (
                center_offset_from_count_inches * 25.4
            )  # Convert to mm to match KiCad SVG coordinate system

            try:
                # Calculate angular offset based on arc position
                delta_angle_from_count = math.degrees(
                    math.asin(center_offset_from_count_mm / node_radius_mm)
                )
            except (ValueError, ZeroDivisionError):
                delta_angle_from_count = 0

            # Calculate final position on circle perimeter
            final_angle = seg_angle + delta_angle_from_count
            x_circleintersect = x_node_mm + node_radius_mm * math.cos(
                math.radians(final_angle)
            )
            y_circleintersect = y_node_mm + node_radius_mm * math.sin(
                math.radians(final_angle)
            )

            # Draw red dot if debug mode is on (use unflipped coordinates)
            if print_circles_and_dots:
                svg_groups.append(
                    f'<circle cx="{x_circleintersect:.3f}" cy="{y_circleintersect:.3f}" r="0.8" fill="red" />'
                )

            # Store the point WITH Y FLIPPED for svg_utils.draw_styled_path()
            points_to_pass_through.setdefault(node_id, {}).setdefault(seg_uuid, {})[
                inst_name
            ] = {
                "x": x_circleintersect,
                "y": -y_circleintersect,  # Flip Y for the paths
            }
            point_count += 1

# === ADD WHITE RECTANGLES TO MASK WIRES ===
# Add white rectangles over each wire segment to mask out the original wires
wire_mask_width_mm = 1  # Width of the mask rectangle in mm

for wire_uuid, wire_coords in wire_locations_scaled.items():
    # Get wire endpoints in inches
    a_x_inches = wire_coords["a_x"]
    a_y_inches = wire_coords["a_y"]
    b_x_inches = wire_coords["b_x"]
    b_y_inches = wire_coords["b_y"]

    # Convert to millimeters for SVG coordinates
    a_x_mm = a_x_inches * 25.4
    a_y_mm = a_y_inches * 25.4
    b_x_mm = b_x_inches * 25.4
    b_y_mm = b_y_inches * 25.4

    # Calculate wire length and angle
    dx = b_x_mm - a_x_mm
    dy = b_y_mm - a_y_mm
    length = math.sqrt(dx * dx + dy * dy)
    angle_rad = math.atan2(dy, dx)
    angle_deg = math.degrees(angle_rad)

    # Calculate rectangle center (midpoint of wire)
    center_x = (a_x_mm + b_x_mm) / 2
    center_y = (a_y_mm + b_y_mm) / 2

    # Create rectangle dimensions
    # Length should extend wire_mask_width_mm beyond each endpoint to ensure full coverage
    rect_length = length + wire_mask_width_mm
    rect_width = wire_mask_width_mm

    # Calculate rectangle corners (rotated around center)
    half_length = rect_length / 2
    half_width = rect_width / 2

    # Corner offsets before rotation
    corners = [
        (-half_length, -half_width),
        (half_length, -half_width),
        (half_length, half_width),
        (-half_length, half_width),
    ]

    # Rotate corners around origin, then translate to center
    rotated_corners = []
    cos_a = math.cos(angle_rad)
    sin_a = math.sin(angle_rad)

    for cx, cy in corners:
        # Rotate
        rx = cx * cos_a - cy * sin_a
        ry = cx * sin_a + cy * cos_a
        # Translate to center
        rotated_corners.append((center_x + rx, center_y + ry))

    # Create SVG rectangle as a polygon (since we need rotation)
    points_str = " ".join([f"{x:.3f},{y:.3f}" for x, y in rotated_corners])
    svg_groups.append(f'<polygon points="{points_str}" fill="#F5F4EF" stroke="none" />')

# === BUILD CLEANED CHAINS AND SVG ===
cleaned_chains = {}

# Iterate over each instance to build its path
for instance in instances:
    path_segments = instance.get("graph_path_segments", [])
    path_directions = instance.get("graph_path_directions", [])

    if not path_segments:
        print(f"Warning: No path segments for {instance.get('instance_name')}")
        continue

    # Use segment UUID as the "parent" key (replacing parent_instance concept)
    # For each segment in the path, the segment UUID is the parent
    point_chain = []

    # Walk through each segment in the path
    for seg_uuid, direction in zip(path_segments, path_directions):
        segment_info = graph["segments"][seg_uuid]
        node_a_id = segment_info["node_at_end_a"]
        node_b_id = segment_info["node_at_end_b"]

        # Get the instance name - this is the instance we're currently processing
        inst_name = instance.get("instance_name")

        # Calculate tangent angle for this segment
        node_a_coords = graph["nodes"][node_a_id]
        node_b_coords = graph["nodes"][node_b_id]
        # Convert from inches to millimeters to match KiCad SVG coordinate system
        dx = (node_b_coords["x"] - node_a_coords["x"]) * 25.4
        dy = (node_b_coords["y"] - node_a_coords["y"]) * 25.4
        # Negate the tangent angle because Y coordinates are flipped when stored in points_to_pass_through
        # When Y is flipped, a vector pointing at angle θ becomes angle -θ
        tangent_ab = -math.degrees(math.atan2(dy, dx))

        if direction == "a_to_b":
            # Get entry point at node A and exit point at node B
            if (
                node_a_id in points_to_pass_through
                and seg_uuid in points_to_pass_through[node_a_id]
                and inst_name in points_to_pass_through[node_a_id][seg_uuid]
            ):
                point_a = points_to_pass_through[node_a_id][seg_uuid][inst_name]
                point_chain.append(
                    {"x": point_a["x"], "y": point_a["y"], "tangent": tangent_ab}
                )
            else:
                print(f"  Missing point A for {inst_name} at {node_a_id}/{seg_uuid}")

            if (
                node_b_id in points_to_pass_through
                and seg_uuid in points_to_pass_through[node_b_id]
                and inst_name in points_to_pass_through[node_b_id][seg_uuid]
            ):
                point_b = points_to_pass_through[node_b_id][seg_uuid][inst_name]
                point_chain.append(
                    {"x": point_b["x"], "y": point_b["y"], "tangent": tangent_ab}
                )
            else:
                print(f"  Missing point B for {inst_name} at {node_b_id}/{seg_uuid}")

        else:  # direction == "b_to_a"
            tangent_ba = tangent_ab + 180
            if tangent_ba > 360:
                tangent_ba -= 360

            # Get entry point at node B and exit point at node A
            if (
                node_b_id in points_to_pass_through
                and seg_uuid in points_to_pass_through[node_b_id]
                and inst_name in points_to_pass_through[node_b_id][seg_uuid]
            ):
                point_b = points_to_pass_through[node_b_id][seg_uuid][inst_name]
                point_chain.append(
                    {"x": point_b["x"], "y": point_b["y"], "tangent": tangent_ba}
                )
            else:
                print(f"  Missing point B for {inst_name} at {node_b_id}/{seg_uuid}")

            if (
                node_a_id in points_to_pass_through
                and seg_uuid in points_to_pass_through[node_a_id]
                and inst_name in points_to_pass_through[node_a_id][seg_uuid]
            ):
                point_a = points_to_pass_through[node_a_id][seg_uuid][inst_name]
                point_chain.append(
                    {"x": point_a["x"], "y": point_a["y"], "tangent": tangent_ba}
                )
            else:
                print(f"  Missing point A for {inst_name} at {node_a_id}/{seg_uuid}")

    if point_chain:
        # Use instance name as the key (segment UUID is the "parent" conceptually)
        instance_name = instance.get("instance_name")
        cleaned_chains[instance_name] = point_chain

        # Get appearance from instance
        appearance_data = instance.get(
            "appearance", {"base_color": "blue", "outline_color": "black"}
        )

        # Draw the styled path
        svg_utils.draw_styled_path(
            point_chain,
            0.003,  # stroke width in inches
            appearance_data,
            svg_groups,
        )

        # Add labels at start (node_at_end_a) and end (node_at_end_b)
        for order in [0, -1]:
            if order == 0:
                # Start of path - use node_at_end_a print_name
                text = instance.get("print_name_at_end_a")
            else:
                # End of path - use node_at_end_b print_name
                text = instance.get("print_name_at_end_b")
            
            # Ensure we have text
            if not text:
                text = "?"
            
            # Get coordinates and tangent from point_chain
            point = point_chain[order]
            x_mm = point["x"]
            y_mm = point["y"]
            tangent = point["tangent"]
            
            svg_groups.append(
                label_svg(
                    x_mm,
                    y_mm,
                    tangent,
                    text,
                    text_color="white",
                    background_color="black",
                    outline="black",
                )
            )
        
        # Add white label in the middle of each segment (each pair of consecutive points)
        # Only add labels for segments longer than the threshold
        instance_print_name = instance.get("print_name")
        if not instance_print_name:
            instance_print_name = "?"
        for i in range(len(point_chain) - 1):
            point_a = point_chain[i]
            point_b = point_chain[i + 1]
            
            # Calculate segment length
            dx = point_b["x"] - point_a["x"]
            dy = point_b["y"] - point_a["y"]
            segment_length_mm = math.sqrt(dx * dx + dy * dy)
            
            # Only add label if segment is long enough
            if segment_length_mm >= MIN_SEGMENT_LENGTH_FOR_LABEL_MM:
                # Calculate midpoint of this segment
                x_mm = (point_a["x"] + point_b["x"]) / 2
                y_mm = (point_a["y"] + point_b["y"]) / 2
                tangent = point_a["tangent"]  # Use the tangent from the first point of the segment
                
                svg_groups.append(
                    label_svg(
                        x_mm,
                        y_mm,
                        tangent,
                        instance_print_name,
                        text_color="black",
                        background_color="white",
                        outline="black",
                    )
                )

    else:
        print(f"Empty chain for {instance.get('instance_name')}")

# === EXPORT KICAD SCHEMATIC TO SVG ===

try:
    import subprocess

    result = subprocess.run(
        [
            "kicad-cli",
            "sch",
            "export",
            "svg",
            "--output",
            dirpath(f"{artifact_id}-kicad-direct-export"),
            schematic_path,
        ],
        capture_output=True,
        text=True,
        check=True,
    )

except subprocess.CalledProcessError as e:
    print("Error exporting KiCad schematic:")
    print(f"  stdout: {e.stdout}")
    print(f"  stderr: {e.stderr}")
except FileNotFoundError:
    print("kicad-cli not found. Install KiCad CLI tools.")

# Wrap the KiCad SVG contents in a group
add_net_overlay_groups_to_svg(path("kicad direct export svg"))

# Extract viewBox and dimensions from KiCad SVG to match coordinate systems
kicad_svg_attrs = extract_svg_viewbox(path("kicad direct export svg"))

# Build SVG opening tag with matching viewBox/width/height
svg_opening = '<svg xmlns="http://www.w3.org/2000/svg" stroke-linecap="round" stroke-linejoin="round"'
if kicad_svg_attrs["viewBox"]:
    svg_opening += f' viewBox="{kicad_svg_attrs["viewBox"]}"'
if kicad_svg_attrs["width"]:
    svg_opening += f' width="{kicad_svg_attrs["width"]}"'
if kicad_svg_attrs["height"]:
    svg_opening += f' height="{kicad_svg_attrs["height"]}"'
svg_opening += ">\n"

# === WRITE SVG OVERLAY OUTPUT ===
svg_output = (
    svg_opening
    + f'  <g id="{artifact_id}-net-overlay-contents-start">\n'
    + "\n".join(svg_groups)
    + "\n  </g>\n"
    + f'  <g id="{artifact_id}-net-overlay-contents-end"/>\n'
    + "</svg>\n"
)

overlay_svg_path = path("net overlay svg")
with open(overlay_svg_path, "w", encoding="utf-8") as f:
    f.write(svg_output)

svg_utils.find_and_replace_svg_group(
    path("net overlay svg"),
    "kicad_sch_parser-net-overlay",
    path("kicad direct export svg"),
    "kicad_sch_parser-net-overlay",
)

# === PRODUCE MULTIPAGE PDF ===
temp_pdfs = []
inkscape_bin = "/Applications/Inkscape.app/Contents/MacOS/inkscape"  # adjust if needed

# Get all SVG files from the directory, sorted for consistent page order
svg_files = sorted(
    [
        f
        for f in os.listdir(dirpath(f"{artifact_id}-kicad-direct-export"))
        if f.endswith(".svg")
        and os.path.isfile(
            os.path.join(dirpath(f"{artifact_id}-kicad-direct-export"), f)
        )
    ]
)

for svg_filename in svg_files:
    svg_path = os.path.join(dirpath(f"{artifact_id}-kicad-direct-export"), svg_filename)
    pdf_path = svg_path.replace(".svg", ".temp.pdf")

    subprocess.run(
        [
            inkscape_bin,
            svg_path,
            "--export-type=pdf",
            f"--export-filename={pdf_path}",
        ],
        check=True,
    )

    temp_pdfs.append(pdf_path)

# Merge all PDFs
subprocess.run(
    ["pdfunite"] + temp_pdfs + [path("output pdf")],
    check=True,
)

# Optional cleanup
for temp in temp_pdfs:
    if os.path.exists(temp):
        os.remove(temp)
