import os
import json
import random
import math
from harnice import fileio
from harnice.utils import svg_utils


def file_structure():
    return {
        f"{fileio.partnumber('pn-rev')}-drawing.svg": "drawing",
        f"{fileio.partnumber('pn-rev')}-attributes.json": "attributes",
    }

def generate_structure():
    pass


def render():
    fileio.set_file_structure(file_structure())
    fileio.verify_revision_structure(product_type="part")
    generate_structure()

    # === ATTRIBUTES JSON DEFAULTS ===
    default_attributes = {
        "csys_parent_prefs": [".node"],
        "tooling_info": {"tools": {}},
        "build_notes": {},
        "csys_children": {
            "accessory-1": {"x": 3, "y": 2, "angle": 0, "rotation": 0},
            "accessory-2": {"x": 2, "y": 3, "angle": 0, "rotation": 0},
            "flagnote-1": {"angle": 0, "distance": 2, "rotation": 0},
            "flagnote-leader-1": {"angle": 0, "distance": 1, "rotation": 0},
            "flagnote-2": {"angle": 15, "distance": 2, "rotation": 0},
            "flagnote-leader-2": {"angle": 15, "distance": 1, "rotation": 0},
            "flagnote-3": {"angle": -15, "distance": 2, "rotation": 0},
            "flagnote-leader-3": {"angle": -15, "distance": 1, "rotation": 0},
            "flagnote-4": {"angle": 30, "distance": 2, "rotation": 0},
            "flagnote-leader-4": {"angle": 30, "distance": 1, "rotation": 0},
            "flagnote-5": {"angle": -30, "distance": 2, "rotation": 0},
            "flagnote-leader-5": {"angle": -30, "distance": 1, "rotation": 0},
            "flagnote-6": {"angle": 45, "distance": 2, "rotation": 0},
            "flagnote-leader-6": {"angle": 45, "distance": 1, "rotation": 0},
            "flagnote-7": {"angle": -45, "distance": 2, "rotation": 0},
            "flagnote-leader-7": {"angle": -45, "distance": 1, "rotation": 0},
            "flagnote-8": {"angle": 60, "distance": 2, "rotation": 0},
            "flagnote-leader-8": {"angle": 60, "distance": 1, "rotation": 0},
            "flagnote-9": {"angle": -60, "distance": 2, "rotation": 0},
            "flagnote-leader-9": {"angle": -60, "distance": 1, "rotation": 0},
            "flagnote-10": {"angle": -75, "distance": 2, "rotation": 0},
            "flagnote-leader-10": {"angle": -75, "distance": 1, "rotation": 0},
            "flagnote-11": {"angle": 75, "distance": 2, "rotation": 0},
            "flagnote-leader-11": {"angle": 75, "distance": 1, "rotation": 0},
            "flagnote-12": {"angle": -90, "distance": 2, "rotation": 0},
            "flagnote-leader-12": {"angle": -90, "distance": 1, "rotation": 0},
            "flagnote-13": {"angle": 90, "distance": 2, "rotation": 0},
            "flagnote-leader-13": {"angle": 90, "distance": 1, "rotation": 0},
            "flagnote-14": {"angle": -105, "distance": 2, "rotation": 0},
            "flagnote-leader-14": {"angle": -105, "distance": 1, "rotation": 0},
            "flagnote-15": {"angle": 105, "distance": 2, "rotation": 0},
            "flagnote-leader-15": {"angle": 105, "distance": 1, "rotation": 0},
            "flagnote-16": {"angle": -120, "distance": 2, "rotation": 0},
            "flagnote-leader-16": {"angle": -120, "distance": 1, "rotation": 0},
        },
    }

    attributes_path = fileio.path("attributes")

    # Load or create attributes.json
    if os.path.exists(attributes_path):
        try:
            with open(attributes_path, "r", encoding="utf-8") as f:
                attrs = json.load(f)
        except Exception as e:
            print(f"[WARNING] Could not load existing attributes.json: {e}")
            attrs = default_attributes.copy()
    else:
        attrs = default_attributes.copy()
        with open(attributes_path, "w", encoding="utf-8") as f:
            json.dump(attrs, f, indent=4)

    # === SVG SETUP ===
    svg_path = fileio.path("drawing")
    temp_svg_path = svg_path + ".tmp"

    svg_width = 400
    svg_height = 400
    group_name = f"{fileio.partnumber('pn')}-drawing"

    random_fill = "#{:06X}".format(random.randint(0, 0xFFFFFF))
    fallback_rect = f'    <rect x="0" y="-48" width="96" height="96" fill="{random_fill}" stroke="black" stroke-width="1"/>'

    csys_children = attrs.get("csys_children", {})

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="{svg_width}" height="{svg_height}">',
        f'  <g id="{group_name}-contents-start">',
        fallback_rect,
        "  </g>",
        f'  <g id="{group_name}-contents-end">',
        "  </g>",
    ]

    # === Render Output Csys Locations ===
    lines.append('  <g id="output csys locations">')

    arrow_len = 24
    dot_radius = 4
    arrow_size = 6

    for csys_name, csys in csys_children.items():
        try:
            x = float(csys.get("x", 0)) * 96
            y = float(csys.get("y", 0)) * 96

            angle_deg = float(csys.get("angle", 0))
            distance_in = float(csys.get("distance", 0))
            angle_rad = math.radians(angle_deg)
            dist_px = distance_in * 96
            x += dist_px * math.cos(angle_rad)
            y += dist_px * math.sin(angle_rad)

            rotation_deg = float(csys.get("rotation", 0))
            rotation_rad = math.radians(rotation_deg)
            cos_r, sin_r = math.cos(rotation_rad), math.sin(rotation_rad)

            dx_x, dy_x = arrow_len * cos_r, arrow_len * sin_r
            dx_y, dy_y = -arrow_len * sin_r, arrow_len * cos_r

            lines.append(f'    <g id="{csys_name}">')
            lines.append(
                f'      <circle cx="{x:.2f}" cy="{-y:.2f}" r="{dot_radius}" fill="black"/>'
            )

            def draw_arrow(x1, y1, dx, dy, color):
                x2, y2 = x1 + dx, y1 + dy
                lines.append(
                    f'      <line x1="{x1:.2f}" y1="{-y1:.2f}" '
                    f'x2="{x2:.2f}" y2="{-y2:.2f}" stroke="{color}" stroke-width="2"/>'
                )
                length = math.hypot(dx, dy)
                if length == 0:
                    return
                ux, uy = dx / length, dy / length
                px, py = -uy, ux
                base_x = x2 - ux * arrow_size
                base_y = y2 - uy * arrow_size
                tip = (x2, y2)
                left = (base_x + px * (arrow_size / 2), base_y + py * (arrow_size / 2))
                right = (base_x - px * (arrow_size / 2), base_y - py * (arrow_size / 2))
                lines.append(
                    f'      <polygon points="{tip[0]:.2f},{-tip[1]:.2f} '
                    f'{left[0]:.2f},{-left[1]:.2f} {right[0]:.2f},{-right[1]:.2f}" fill="{color}"/>'
                )

            draw_arrow(x, y, dx_x, dy_x, "red")
            draw_arrow(x, y, dx_y, dy_y, "green")
            lines.append("    </g>")

        except Exception as e:
            print(f"[WARNING] Failed to render csys {csys_name}: {e}")

    lines.append("  </g>")
    lines.append("</svg>")

    with open(temp_svg_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    if os.path.exists(svg_path):
        try:
            with open(svg_path, "r", encoding="utf-8") as f:
                svg_text = f.read()
        except Exception:
            svg_text = ""

        if (
            f"{group_name}-contents-start" not in svg_text
            or f"{group_name}-contents-end" not in svg_text
        ):
            svg_utils.add_entire_svg_file_contents_to_group(svg_path, group_name)

        svg_utils.find_and_replace_svg_group(
            target_svg_filepath=temp_svg_path,
            source_svg_filepath=svg_path,
            source_group_name=group_name,
            destination_group_name=group_name,
        )

    if os.path.exists(svg_path):
        os.remove(svg_path)
    os.rename(temp_svg_path, svg_path)

    print()
    print(f"Part file '{fileio.partnumber('pn')}' updated")
    print()
