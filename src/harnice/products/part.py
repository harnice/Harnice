import os
import json
import random
import math
import re
from PIL import Image, ImageDraw, ImageFont
from harnice import fileio, state
from harnice.utils import svg_utils


default_desc = "COTS COMPONENT, SIZE, COLOR, etc."


def file_structure():
    return {
        f"{state.partnumber('pn-rev')}-drawing.svg": "drawing",
        f"{state.partnumber('pn-rev')}-drawing.png": "drawing png",
        f"{state.partnumber('pn-rev')}-attributes.json": "attributes",
    }


def generate_structure():
    pass


def render():
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
    group_name = f"{state.partnumber('pn')}-drawing"

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
            source_svg_filepath=svg_path,
            source_group_name=group_name,
            destination_svg_filepath=temp_svg_path,
            destination_group_name=group_name,
        )

    if os.path.exists(svg_path):
        os.remove(svg_path)
    os.rename(temp_svg_path, svg_path)


    # ==================================================
    # PNG generation
    # ==================================================

    # === Step X: PNG Rendering Including Parsed SVG Contents Group ===

    # ------------------------------------------------------------------
    # 1. Extract raw contents group from final SVG
    # ------------------------------------------------------------------
    with open(svg_path, "r", encoding="utf-8") as f:
        svg_text = f.read()

    start_tag = f'<g id="{group_name}-contents-start">'
    end_tag   = f'<g id="{group_name}-contents-end">'

    start_idx = svg_text.find(start_tag)
    end_idx   = svg_text.find(end_tag)

    if start_idx == -1 or end_idx == -1:
        print("[WARNING] Could not find contents group in SVG — PNG will only draw csys.")
        inner_svg = ""
    else:
        inner_svg = svg_text[start_idx + len(start_tag): end_idx]

    # ------------------------------------------------------------------
    # 2. Parse simple shapes from the SVG content group
    # ------------------------------------------------------------------
    parsed_shapes = []

    def get_attr(tag, name, default=None):
        m = re.search(fr'{name}="([^"]+)"', tag)
        return m.group(1) if m else default

    # <rect>
    for tag in re.findall(r"<rect[^>]*/?>", inner_svg):
        parsed_shapes.append((
            "rect",
            {
                "x": float(get_attr(tag, "x", 0)),
                "y": float(get_attr(tag, "y", 0)),
                "w": float(get_attr(tag, "width", 0)),
                "h": float(get_attr(tag, "height", 0)),
                "fill": get_attr(tag, "fill", "none"),
                "stroke": get_attr(tag, "stroke", None),
                "sw": float(get_attr(tag, "stroke-width", 1) or 1)
            }
        ))

    # <circle>
    for tag in re.findall(r"<circle[^>]*/?>", inner_svg):
        parsed_shapes.append((
            "circle",
            {
                "cx": float(get_attr(tag, "cx", 0)),
                "cy": float(get_attr(tag, "cy", 0)),
                "r": float(get_attr(tag, "r", 0)),
                "fill": get_attr(tag, "fill", "none"),
                "stroke": get_attr(tag, "stroke", None),
                "sw": float(get_attr(tag, "stroke-width", 1) or 1)
            }
        ))

    # <line>
    for tag in re.findall(r"<line[^>]*/?>", inner_svg):
        parsed_shapes.append((
            "line",
            {
                "x1": float(get_attr(tag, "x1", 0)),
                "y1": float(get_attr(tag, "y1", 0)),
                "x2": float(get_attr(tag, "x2", 0)),
                "y2": float(get_attr(tag, "y2", 0)),
                "stroke": get_attr(tag, "stroke", "black"),
                "sw": float(get_attr(tag, "stroke-width", 1) or 1)
            }
        ))

    # <polygon>
    for tag in re.findall(r"<polygon[^>]*/?>", inner_svg):
        pts = []
        pts_raw = get_attr(tag, "points", "")
        for p in pts_raw.split():
            if "," in p:
                xx, yy = p.split(",")
                pts.append((float(xx), float(yy)))

        parsed_shapes.append((
            "polygon",
            {
                "points": pts,
                "fill": get_attr(tag, "fill", "none"),
                "stroke": get_attr(tag, "stroke", None)
            }
        ))

    # <text>
    for full_tag in re.findall(r'<text[^>]*>.*?</text>', inner_svg, flags=re.DOTALL):
        text_content = re.sub(r'<.*?>', '', full_tag).strip()
        parsed_shapes.append((
            "text",
            {
                "x": float(get_attr(full_tag, "x", 0)),
                "y": float(get_attr(full_tag, "y", 0)),
                "text": text_content,
                "fill": get_attr(full_tag, "fill", "black")
            }
        ))

    # ------------------------------------------------------------------
    # 3. Compute bounding box from both SVG shapes and csys
    # ------------------------------------------------------------------
    padding = 50
    scale   = 96

    pts = []

    # Shapes
    for typ, p in parsed_shapes:
        if typ == "rect":
            pts += [(p["x"], p["y"]), (p["x"] + p["w"], p["y"] + p["h"])]
        elif typ == "circle":
            pts += [(p["cx"]-p["r"], p["cy"]-p["r"]),
                    (p["cx"]+p["r"], p["cy"]+p["r"])]
        elif typ == "line":
            pts += [(p["x1"], p["y1"]), (p["x2"], p["y2"])]
        elif typ == "polygon":
            pts += p["points"]
        elif typ == "text":
            pts.append((p["x"], p["y"]))

    # Csys (mix of up/down coordinates)
    for csys_name, csys in csys_children.items():
        x = float(csys.get("x", 0)) * scale
        y = float(csys.get("y", 0)) * scale
        angle = math.radians(float(csys.get("angle", 0)))
        dist  = float(csys.get("distance", 0)) * scale
        x += dist * math.cos(angle)
        y += dist * math.sin(angle)

        pts.append((x, y))

        rot = math.radians(float(csys.get("rotation", 0)))
        ax = x + 24 * math.cos(rot)
        ay = y + 24 * math.sin(rot)
        bx = x - 24 * math.sin(rot)
        by = y + 24 * math.cos(rot)
        pts += [(ax, ay), (bx, by)]

    if not pts:
        pts = [(0, 0)]

    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]

    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    width  = int((max_x - min_x) + 2 * padding)
    height = int((max_y - min_y) + 2 * padding)

    # ------------------------------------------------------------------
    # 3B. Mapping functions
    # ------------------------------------------------------------------

    # SVG is already Y-down → no flip
    def map_svg_xy(x, y):
        return (
            int((x - min_x) + padding),
            int((y - min_y) + padding)
        )

    # CSYS is Y-up → must be flipped
    def map_csys_xy(x, y):
        return (
            int((x - min_x) + padding),
            int(height - ((y - min_y) + padding))
        )


    # ------------------------------------------------------------------
    # 4. Create PNG and draw SVG shapes (NO Y FLIP)
    # ------------------------------------------------------------------
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("Arial.ttf", 8)
    except:
        font = ImageFont.load_default()

    for typ, p in parsed_shapes:

        if typ == "rect":
            x1, y1 = map_svg_xy(p["x"], p["y"])
            x2, y2 = map_svg_xy(p["x"] + p["w"], p["y"] + p["h"])
            draw.rectangle((x1, y1, x2, y2), fill=p["fill"], outline=p["stroke"], width=int(p["sw"]))

        elif typ == "circle":
            cx, cy = map_svg_xy(p["cx"], p["cy"])
            r = p["r"]
            draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=p["fill"], outline=p["stroke"], width=int(p["sw"]))

        elif typ == "line":
            x1, y1 = map_svg_xy(p["x1"], p["y1"])
            x2, y2 = map_svg_xy(p["x2"], p["y2"])
            draw.line((x1, y1, x2, y2), fill=p["stroke"], width=int(p["sw"]))

        elif typ == "polygon":
            pts2 = [map_svg_xy(x, y) for x, y in p["points"]]
            draw.polygon(pts2, fill=p["fill"], outline=p["stroke"])

        elif typ == "text":
            x_txt, y_txt = map_svg_xy(p["x"], p["y"])
            draw.text((x_txt, y_txt), p["text"], fill=p["fill"], font=font)


    # ------------------------------------------------------------------
    # 5. Draw CSYS arrows/dots (WITH Y FLIP)
    # ------------------------------------------------------------------
    arrow_len = 24
    dot_radius = 4

    for csys_name, csys in csys_children.items():
        try:
            x = float(csys.get("x", 0)) * scale
            y = float(csys.get("y", 0)) * scale
            angle = math.radians(float(csys.get("angle", 0)))
            dist  = float(csys.get("distance", 0)) * scale

            x += dist * math.cos(angle)
            y += dist * math.sin(angle)

            rot = math.radians(float(csys.get("rotation", 0)))

            cx, cy = map_csys_xy(x, y)

            # Dot
            draw.ellipse(
                (cx - dot_radius, cy - dot_radius, cx + dot_radius, cy + dot_radius),
                fill="black"
            )

            # X arrow
            x2 = x + arrow_len * math.cos(rot)
            y2 = y + arrow_len * math.sin(rot)
            px1, py1 = map_csys_xy(x2, y2)
            draw.line((cx, cy, px1, py1), fill="red", width=2)

            # Y arrow
            x3 = x - arrow_len * math.sin(rot)
            y3 = y + arrow_len * math.cos(rot)
            px2, py2 = map_csys_xy(x3, y3)
            draw.line((cx, cy, px2, py2), fill="green", width=2)

            draw.text((cx + 6, cy - 6), csys_name, fill="blue", font=font)

        except Exception as e:
            print(f"[WARNING] PNG csys draw failed for {csys_name}: {e}")

    # ------------------------------------------------------------------
    # 6. Save PNG
    # ------------------------------------------------------------------
    png_path = fileio.path("drawing png")
    img.save(png_path, dpi=(1000, 1000))




    print()
    print(f"Part file '{state.partnumber('pn')}' updated")
    print()
