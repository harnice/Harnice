import os
import re
import math

def add_entire_svg_file_contents_to_group(filepath, new_group_name):
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as file:
                svg_content = file.read()

            match = re.search(r"<svg[^>]*>(.*?)</svg>", svg_content, re.DOTALL)
            if not match:
                raise ValueError(
                    "File does not appear to be a valid SVG or has no inner contents."
                )
            inner_content = match.group(1).strip()

            updated_svg_content = (
                f'<svg xmlns="http://www.w3.org/2000/svg">\n'
                f'  <g id="{new_group_name}-contents-start">\n'
                f"    {inner_content}\n"
                f"  </g>\n"
                f'  <g id="{new_group_name}-contents-end"></g>\n'
                f"</svg>\n"
            )

            with open(filepath, "w", encoding="utf-8") as file:
                file.write(updated_svg_content)

        except Exception as e:
            print(
                f"Error adding contents of {os.path.basename(filepath)} to a new group {new_group_name}: {e}"
            )
    else:
        print(
            f"Trying to add contents of {os.path.basename(filepath)} to a new group but file does not exist."
        )


def find_and_replace_svg_group(
    target_svg_filepath, source_svg_filepath, source_group_name, destination_group_name
):
    with open(source_svg_filepath, "r", encoding="utf-8") as source_file:
        source_svg_content = source_file.read()
    with open(target_svg_filepath, "r", encoding="utf-8") as target_file:
        target_svg_content = target_file.read()

    source_start_tag = f'id="{source_group_name}-contents-start"'
    source_end_tag = f'id="{source_group_name}-contents-end"'
    dest_start_tag = f'id="{destination_group_name}-contents-start"'
    dest_end_tag = f'id="{destination_group_name}-contents-end"'

    source_start_index = source_svg_content.find(source_start_tag)
    if source_start_index == -1:
        raise ValueError(
            f"[ERROR] Source start tag <{source_start_tag}> not found in <{source_svg_filepath}>."
        )
    source_start_index = source_svg_content.find(">", source_start_index) + 1

    source_end_index = source_svg_content.find(source_end_tag)
    if source_end_index == -1:
        raise ValueError(
            f"[ERROR] Source end tag <{source_end_tag}> not found in <{source_svg_filepath}>."
        )
    source_end_index = source_svg_content.rfind("<", 0, source_end_index)

    dest_start_index = target_svg_content.find(dest_start_tag)
    if dest_start_index == -1:
        raise ValueError(
            f"[ERROR] Target start tag <{dest_start_tag}> not found in <{target_svg_filepath}>."
        )
    dest_start_index = target_svg_content.find(">", dest_start_index) + 1

    dest_end_index = target_svg_content.find(dest_end_tag)
    if dest_end_index == -1:
        raise ValueError(
            f"[ERROR] Target end tag <{dest_end_tag}> not found in <{target_svg_filepath}>."
        )
    dest_end_index = target_svg_content.rfind("<", 0, dest_end_index)

    replacement_group_content = source_svg_content[source_start_index:source_end_index]

    updated_svg_content = (
        target_svg_content[:dest_start_index]
        + replacement_group_content
        + target_svg_content[dest_end_index:]
    )

    with open(target_svg_filepath, "w", encoding="utf-8") as updated_file:
        updated_file.write(updated_svg_content)

    return 1

def draw_styled_path(spline_points, stroke_width, appearance_dict, local_group):
    """
    Draws a straight or curved (spline) path with full appearance styling.
    spline_points: list of dicts [{x, y, tangent}], minimum 2 points
    stroke_width: numeric width of the base line
    appearance_dict: normalized dictionary (from appearance.parse)
    local_group: list to append SVG line/curve elements to
    """

    if not appearance_dict:
        appearance_dict = {"base_color": "black"}

    # ---------------------------------------------------------------------
    # --- helper: convert spline to SVG path
    # ---------------------------------------------------------------------
    def spline_to_path(points):
        """Return SVG 'd' attribute using cubic Beziers from point chain."""
        if len(points) < 2:
            return ""
        path = f"M {points[0]['x']:.3f},{-points[0]['y']:.3f}"
        for i in range(len(points) - 1):
            p0 = points[i]
            p1 = points[i + 1]
            t0 = math.radians(p0.get("tangent", 0))
            t1 = math.radians(p1.get("tangent", 0))
            d = math.hypot(p1["x"] - p0["x"], p1["y"] - p0["y"])
            ctrl_dist = d * 0.5
            c1x = p0["x"] + math.cos(t0) * ctrl_dist
            c1y = p0["y"] + math.sin(t0) * ctrl_dist
            c2x = p1["x"] - math.cos(t1) * ctrl_dist
            c2y = p1["y"] - math.sin(t1) * ctrl_dist
            path += f" C {c1x:.3f},{-c1y:.3f} {c2x:.3f},{-c2y:.3f} {p1['x']:.3f},{-p1['y']:.3f}"
        return path

    # ---------------------------------------------------------------------
    # --- helper: hatch lines
    # ---------------------------------------------------------------------
    def add_hatch_lines_along_path(points, hatch_angle, stroke_width, color="black"):
        """Approximate by hatching between each adjacent point pair."""
        for i in range(len(points) - 1):
            x1, y1 = points[i]["x"], points[i]["y"]
            x2, y2 = points[i + 1]["x"], points[i + 1]["y"]
            dx, dy = x2 - x1, y2 - y1
            seg_len = math.hypot(dx, dy)
            ux, uy = dx / seg_len, dy / seg_len
            nx, ny = -uy, ux

            theta = math.radians(hatch_angle)
            hx = nx * math.cos(theta) - ny * math.sin(theta)
            hy = nx * math.sin(theta) + ny * math.cos(theta)

            spacing = stroke_width * 1.5
            hatch_length = stroke_width / abs(math.cos(theta))
            num_hatches = int(seg_len // spacing) + 1
            for j in range(num_hatches):
                t = j * spacing
                cx = x1 + ux * t
                cy = y1 + uy * t
                hx1 = cx - hx * (hatch_length / 2)
                hy1 = cy - hy * (hatch_length / 2)
                hx2 = cx + hx * (hatch_length / 2)
                hy2 = cy + hy * (hatch_length / 2)
                local_group.append(
                    f'<line x1="{hx1:.2f}" y1="{-hy1:.2f}" '
                    f'x2="{hx2:.2f}" y2="{-hy2:.2f}" '
                    f'stroke="{color}" stroke-width="0.2" />'
                )

    # ---------------------------------------------------------------------
    # --- Draw main body
    # ---------------------------------------------------------------------
    base_color = appearance_dict.get("base_color", "black")
    outline_color = appearance_dict.get("outline_color")
    path_d = spline_to_path(spline_points)

    if outline_color:
        local_group.append(
            f'<path d="{path_d}" stroke="{outline_color}" stroke-width="{stroke_width}" '
            f'fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
        )
        stroke_width -= 1.5

    local_group.append(
        f'<path d="{path_d}" stroke="{base_color}" stroke-width="{stroke_width}" '
        f'fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
    )

    # ---------------------------------------------------------------------
    # --- Add pattern overlays
    # ---------------------------------------------------------------------
    if appearance_dict.get("parallelstripe"):
        stripes = appearance_dict["parallelstripe"]
        num = len(stripes)
        stripe_thickness = 0.5
        stripe_spacing = stroke_width / num
        offset = -(num - 1) * stripe_spacing / 2
        for color in stripes:
            local_group.append(
                f'<path d="{path_d}" stroke="{color}" '
                f'stroke-width="{stripe_thickness}" fill="none" '
                f'transform="translate(0,{offset:.2f})"/>'
            )
            offset += stripe_spacing

    if appearance_dict.get("perpstripe"):
        stripes = appearance_dict["perpstripe"]
        num = len(stripes)
        pattern_length = 30
        dash = pattern_length / (num + 1)
        gap = pattern_length - dash
        offset = 0
        for color in stripes:
            offset += dash
            local_group.append(
                f'<path d="{path_d}" stroke="{color}" stroke-width="{stroke_width}" '
                f'stroke-dasharray="{dash},{gap}" stroke-dashoffset="{offset}" '
                f'fill="none" />'
            )

    # ---------------------------------------------------------------------
    # --- Twist hatch (RH/LH)
    # ---------------------------------------------------------------------
    if appearance_dict.get("twisted") == "RH":
        add_hatch_lines_along_path(spline_points, 70, stroke_width)
    elif appearance_dict.get("twisted") == "LH":
        add_hatch_lines_along_path(spline_points, -70, stroke_width)
