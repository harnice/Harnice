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
    # PNG generation (SVG is source-of-truth for graphics;
    # CSYS JSON is source-of-truth for axes, expressed in inches)
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
        inner_svg = svg_text[start_idx + len(start_tag) : end_idx]


    # ------------------------------------------------------------------
    # 2. Helpers for SVG attribute + transform parsing
    # ------------------------------------------------------------------
    parsed_shapes = []  # list of (type, params_dict) in *SVG pixel coords*

    def get_attr(tag, name, default=None):
        m = re.search(fr'{name}="([^"]+)"', tag)
        return m.group(1) if m else default

    def _parse_floats(s):
        return [float(x) for x in re.split(r"[ ,]+", s.strip()) if x]

    def _mat_identity():
        return [
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
        ]

    def _mat_mul(a, b):
        """3x3 matrix multiply: result = a @ b."""
        res = [[0.0, 0.0, 0.0] for _ in range(3)]
        for i in range(3):
            for j in range(3):
                res[i][j] = (
                    a[i][0] * b[0][j] +
                    a[i][1] * b[1][j] +
                    a[i][2] * b[2][j]
                )
        return res

    def _mat_apply(m, x, y):
        """Apply 3x3 matrix to (x, y)."""
        nx = m[0][0] * x + m[0][1] * y + m[0][2]
        ny = m[1][0] * x + m[1][1] * y + m[1][2]
        return nx, ny

    def parse_transform(transform_str):
        """Parse an SVG transform string into a 3x3 matrix."""
        if not transform_str:
            return _mat_identity()

        mat = _mat_identity()
        for op, args_str in re.findall(r'(matrix|translate|scale|rotate|skewX|skewY)\s*\(([^)]*)\)', transform_str):
            nums = _parse_floats(args_str)
            op = op.lower()

            if op == "matrix" and len(nums) == 6:
                a, b, c, d, e, f = nums
                m2 = [
                    [a, c, e],
                    [b, d, f],
                    [0.0, 0.0, 1.0],
                ]

            elif op == "translate":
                tx = nums[0] if len(nums) > 0 else 0.0
                ty = nums[1] if len(nums) > 1 else 0.0
                m2 = [
                    [1.0, 0.0, tx],
                    [0.0, 1.0, ty],
                    [0.0, 0.0, 1.0],
                ]

            elif op == "scale":
                sx = nums[0] if len(nums) > 0 else 1.0
                sy = nums[1] if len(nums) > 1 else sx
                m2 = [
                    [sx, 0.0, 0.0],
                    [0.0, sy, 0.0],
                    [0.0, 0.0, 1.0],
                ]

            elif op == "rotate":
                angle = nums[0] if nums else 0.0
                rad = math.radians(angle)
                cos_a, sin_a = math.cos(rad), math.sin(rad)
                if len(nums) == 3:
                    cx, cy = nums[1], nums[2]
                    # T(cx,cy) * R(angle) * T(-cx,-cy)
                    t1 = [
                        [1.0, 0.0, cx],
                        [0.0, 1.0, cy],
                        [0.0, 0.0, 1.0],
                    ]
                    r  = [
                        [cos_a, -sin_a, 0.0],
                        [sin_a,  cos_a, 0.0],
                        [0.0,    0.0,   1.0],
                    ]
                    t2 = [
                        [1.0, 0.0, -cx],
                        [0.0, 1.0, -cy],
                        [0.0, 0.0, 1.0],
                    ]
                    m2 = _mat_mul(_mat_mul(t1, r), t2)
                else:
                    m2 = [
                        [cos_a, -sin_a, 0.0],
                        [sin_a,  cos_a, 0.0],
                        [0.0,    0.0,   1.0],
                    ]

            elif op == "skewx":
                angle = nums[0] if nums else 0.0
                t = math.tan(math.radians(angle))
                m2 = [
                    [1.0, t,   0.0],
                    [0.0, 1.0, 0.0],
                    [0.0, 0.0, 1.0],
                ]

            elif op == "skewy":
                angle = nums[0] if nums else 0.0
                t = math.tan(math.radians(angle))
                m2 = [
                    [1.0, 0.0, 0.0],
                    [t,   1.0, 0.0],
                    [0.0, 0.0, 1.0],
                ]

            else:
                m2 = _mat_identity()

            # Left-to-right application in SVG row-vector sense:
            mat = _mat_mul(mat, m2)

        return mat


    # ------------------------------------------------------------------
    # 3. Parse shapes from the SVG contents group (into SVG coords)
    # ------------------------------------------------------------------

    # <rect> → rect or polygon if transformed
    for tag in re.findall(r"<rect[^>]*/?>", inner_svg):
        x = float(get_attr(tag, "x", 0))
        y = float(get_attr(tag, "y", 0))
        w = float(get_attr(tag, "width", 0))
        h = float(get_attr(tag, "height", 0))
        fill = get_attr(tag, "fill", "none")
        stroke = get_attr(tag, "stroke", None)
        stroke_w = float(get_attr(tag, "stroke-width", 1) or 1)
        transform_str = get_attr(tag, "transform", "")

        if transform_str:
            mat = parse_transform(transform_str)
            base_pts = [
                (x,       y),
                (x + w,   y),
                (x + w,   y + h),
                (x,       y + h),
            ]
            pts_tr = [_mat_apply(mat, px, py) for (px, py) in base_pts]
            parsed_shapes.append(("polygon", {
                "points": pts_tr,
                "fill": fill,
                "stroke": stroke,
                "sw": stroke_w,
            }))
        else:
            parsed_shapes.append(("rect", {
                "x": x, "y": y, "w": w, "h": h,
                "fill": fill, "stroke": stroke, "sw": stroke_w,
            }))

    # <circle>
    for tag in re.findall(r"<circle[^>]*/?>", inner_svg):
        cx = float(get_attr(tag, "cx", 0))
        cy = float(get_attr(tag, "cy", 0))
        r  = float(get_attr(tag, "r", 0))
        fill = get_attr(tag, "fill", "none")
        stroke = get_attr(tag, "stroke", None)
        stroke_w = float(get_attr(tag, "stroke-width", 1) or 1)
        transform_str = get_attr(tag, "transform", "")

        if transform_str:
            mat = parse_transform(transform_str)
            cx, cy = _mat_apply(mat, cx, cy)

        parsed_shapes.append(("circle", {
            "cx": cx, "cy": cy, "r": r,
            "fill": fill, "stroke": stroke, "sw": stroke_w,
        }))

    # <line>
    for tag in re.findall(r"<line[^>]*/?>", inner_svg):
        x1 = float(get_attr(tag, "x1", 0))
        y1 = float(get_attr(tag, "y1", 0))
        x2 = float(get_attr(tag, "x2", 0))
        y2 = float(get_attr(tag, "y2", 0))
        stroke = get_attr(tag, "stroke", "black")
        stroke_w = float(get_attr(tag, "stroke-width", 1) or 1)
        transform_str = get_attr(tag, "transform", "")

        if transform_str:
            mat = parse_transform(transform_str)
            x1, y1 = _mat_apply(mat, x1, y1)
            x2, y2 = _mat_apply(mat, x2, y2)

        parsed_shapes.append(("line", {
            "x1": x1, "y1": y1, "x2": x2, "y2": y2,
            "stroke": stroke, "sw": stroke_w,
        }))

    # <polygon>
    for tag in re.findall(r"<polygon[^>]*/?>", inner_svg):
        pts_raw = get_attr(tag, "points", "")
        pts = []
        for p in pts_raw.split():
            if "," in p:
                xx, yy = p.split(",")
                pts.append((float(xx), float(yy)))
        fill = get_attr(tag, "fill", "none")
        stroke = get_attr(tag, "stroke", None)
        stroke_w = float(get_attr(tag, "stroke-width", 1) or 1)
        transform_str = get_attr(tag, "transform", "")

        if transform_str:
            mat = parse_transform(transform_str)
            pts = [_mat_apply(mat, px, py) for (px, py) in pts]

        parsed_shapes.append(("polygon", {
            "points": pts, "fill": fill, "stroke": stroke, "sw": stroke_w,
        }))

    # <text>
    for full_tag in re.findall(r'<text[^>]*>.*?</text>', inner_svg, flags=re.DOTALL):
        txt = re.sub(r'<.*?>', '', full_tag)
        x = float(get_attr(full_tag, "x", 0))
        y = float(get_attr(full_tag, "y", 0))
        fill = get_attr(full_tag, "fill", "black")
        transform_str = get_attr(full_tag, "transform", "")

        if transform_str:
            mat = parse_transform(transform_str)
            x, y = _mat_apply(mat, x, y)

        parsed_shapes.append(("text", {
            "x": x, "y": y, "text": txt.strip(), "fill": fill,
        }))


    # ------------------------------------------------------------------
    # 4. CSYS: convert JSON inches → SVG pixels (y-down)
    # ------------------------------------------------------------------
    padding = 50
    scale   = 96  # px per inch

    def csys_svg_xy(csys):
        """Return CSYS location in SVG pixel coordinates.

        JSON uses inches, x+ right, y+ up, angle ccw.
        SVG uses pixels, x+ right, y+ DOWN.

        If x,y given → use them (in inches).
        Else if distance,angle given → use polar.
        """
        raw_x = csys.get("x")
        raw_y = csys.get("y")
        raw_d = csys.get("distance")
        raw_a = csys.get("angle")

        if raw_x not in ("", None) and raw_y not in ("", None):
            x_in = float(raw_x)
            y_in = float(raw_y)
        elif raw_d not in ("", None) and raw_a not in ("", None):
            dist = float(raw_d)
            ang  = math.radians(float(raw_a))
            x_in = dist * math.cos(ang)
            y_in = dist * math.sin(ang)
        else:
            x_in = 0.0
            y_in = 0.0

        # inches → pixels; y+ up → y+ down
        x_px = x_in * scale
        y_px = -y_in * scale
        return x_px, y_px

    def csys_svg_axes_endpoints(csys, base_x, base_y, arrow_len_px):
        """Return SVG coords for X and Y arrow endpoints for this CSYS."""
        rot_deg = float(csys.get("rotation", 0) or 0)
        rot = math.radians(rot_deg)

        # In CSYS: x-axis = (cos, sin), y-axis = (-sin, cos), y+ up.
        # Map to SVG y-down: (dx, dy) → (dx, -dy).
        dx_x = math.cos(rot) * arrow_len_px
        dy_x = -math.sin(rot) * arrow_len_px

        dx_y = -math.sin(rot) * arrow_len_px
        dy_y = -math.cos(rot) * arrow_len_px

        x_x = base_x + dx_x
        y_x = base_y + dy_x

        x_y = base_x + dx_y
        y_y = base_y + dy_y

        return (x_x, y_x), (y_x, y_y)


    # ------------------------------------------------------------------
    # 5. Compute bounding box from shapes + CSYS (all in SVG coords)
    # ------------------------------------------------------------------
    pts = []

    # Shapes
    for typ, p in parsed_shapes:
        if typ == "rect":
            pts += [(p["x"], p["y"]), (p["x"] + p["w"], p["y"] + p["h"])]
        elif typ == "circle":
            pts += [(p["cx"] - p["r"], p["cy"] - p["r"]),
                    (p["cx"] + p["r"], p["cy"] + p["r"])]
        elif typ == "line":
            pts += [(p["x1"], p["y1"]), (p["x2"], p["y2"])]
        elif typ == "polygon":
            pts += p["points"]
        elif typ == "text":
            pts.append((p["x"], p["y"]))

    # CSYS
    arrow_len_svg = 24  # px in SVG space
    for csys_name, csys in csys_children.items():
        bx, by = csys_svg_xy(csys)
        pts.append((bx, by))
        (x_x, y_x), (x_y, y_y) = csys_svg_axes_endpoints(csys, bx, by, arrow_len_svg)
        pts += [(x_x, y_x), (x_y, y_y)]

    if not pts:
        pts = [(0, 0)]

    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]

    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    width  = int((max_x - min_x) + 2 * padding)
    height = int((max_y - min_y) + 2 * padding)

    def map_xy(x, y):
        """Map SVG pixel coords → PNG pixel coords (same orientation)."""
        return (
            int((x - min_x) + padding),
            int((y - min_y) + padding),
        )


    # ------------------------------------------------------------------
    # 6. Create PNG canvas and draw SVG shapes
    # ------------------------------------------------------------------
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("Arial.ttf", 8)
    except Exception:
        font = ImageFont.load_default()

    for typ, p in parsed_shapes:
        if typ == "rect":
            x1, y1 = map_xy(p["x"], p["y"])
            x2, y2 = map_xy(p["x"] + p["w"], p["y"] + p["h"])
            draw.rectangle(
                (x1, y1, x2, y2),
                fill=p["fill"],
                outline=p["stroke"],
                width=int(p["sw"]),
            )

        elif typ == "circle":
            cx, cy = map_xy(p["cx"], p["cy"])
            r = p["r"]
            draw.ellipse(
                (cx - r, cy - r, cx + r, cy + r),
                fill=p["fill"],
                outline=p["stroke"],
                width=int(p["sw"]),
            )

        elif typ == "line":
            x1, y1 = map_xy(p["x1"], p["y1"])
            x2, y2 = map_xy(p["x2"], p["y2"])
            draw.line((x1, y1, x2, y2), fill=p["stroke"], width=int(p["sw"]))

        elif typ == "polygon":
            pts2 = [map_xy(x, y) for (x, y) in p["points"]]
            draw.polygon(pts2, fill=p["fill"], outline=p["stroke"])

        elif typ == "text":
            x_txt, y_txt = map_xy(p["x"], p["y"])
            draw.text((x_txt, y_txt), p["text"], fill=p["fill"], font=font)


    # ------------------------------------------------------------------
    # 7. Draw CSYS axes/dots on top (in same frame)
    # ------------------------------------------------------------------
    dot_radius = 4

    for csys_name, csys in csys_children.items():
        try:
            bx, by = csys_svg_xy(csys)
            cx, cy = map_xy(bx, by)

            # Dot
            draw.ellipse(
                (cx - dot_radius, cy - dot_radius,
                cx + dot_radius, cy + dot_radius),
                fill="black",
            )

            # Axes endpoints in SVG coords, then mapped
            (x_x, y_x), (x_y, y_y) = csys_svg_axes_endpoints(csys, bx, by, arrow_len_svg)

            px1, py1 = map_xy(x_x, y_x)  # X axis endpoint
            px2, py2 = map_xy(x_y, y_y)  # Y axis endpoint

            # X arrow (red)
            draw.line((cx, cy, px1, py1), fill="red", width=2)

            # Y arrow (green)
            draw.line((cx, cy, px2, py2), fill="green", width=2)

            # Label
            draw.text((cx + 6, cy - 6), csys_name, fill="blue", font=font)

        except Exception as e:
            print(f"[WARNING] PNG csys draw failed for {csys_name}: {e}")


    # ------------------------------------------------------------------
    # 8. Save PNG
    # ------------------------------------------------------------------
    png_path = fileio.path("drawing png")
    img.save(png_path, dpi=(1000, 1000))


    print()
    print(f"Part file '{state.partnumber('pn')}' updated")
    print()
