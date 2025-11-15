import os
import re
import math
from harnice.utils import appearance

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


def draw_styled_path(spline_points, stroke_width_inches, appearance_dict, local_group):
    """
    Draws a spline path with appearance styling.
    Supports left-hand (LH) and right-hand (RH) twisted wire hatching
    with uniform line density and consistent diagonal direction.
    """

    if not appearance_dict:
        appearance_dict = appearance.parse("{'base_color':'red', 'perpstripe':['orange','yellow','green','blue','purple']}")
        stroke_width_inches = 0.01
    else:
        appearance_dict = appearance.parse(appearance_dict)

    # ---------------------------------------------------------------------
    # --- helper: spline_to_path
    # ---------------------------------------------------------------------
    def spline_to_path(points):
        if len(points) < 2:
            return ""
        path = f"M {points[0]['x']:.3f},{-points[0]['y']:.3f}"
        for i in range(len(points) - 1):
            p0, p1 = points[i], points[i + 1]
            t0, t1 = math.radians(p0.get("tangent", 0)), math.radians(
                p1.get("tangent", 0)
            )
            d = math.hypot(p1["x"] - p0["x"], p1["y"] - p0["y"])
            ctrl_dist = d * 0.5
            c1x = p0["x"] + math.cos(t0) * ctrl_dist
            c1y = p0["y"] + math.sin(t0) * ctrl_dist
            c2x = p1["x"] - math.cos(t1) * ctrl_dist
            c2y = p1["y"] - math.sin(t1) * ctrl_dist
            path += f" C {c1x:.3f},{-c1y:.3f} {c2x:.3f},{-c2y:.3f} {p1['x']:.3f},{-p1['y']:.3f}"
        return path

    # ---------------------------------------------------------------------
    # --- helper: draw consistent slanted hatches (twisted wire)
    # ---------------------------------------------------------------------
    def draw_slash_lines(points, slash_lines_dict):
        if slash_lines_dict.get("direction") in ("RH", "LH"):
            if slash_lines_dict.get("angle") is not None:
                angle_slant = slash_lines_dict.get("angle")
            else:
                angle_slant = 20
            if slash_lines_dict.get("step") is not None:
                step_dist = slash_lines_dict.get("step")
            else:
                step_dist = stroke_width * 3
            if slash_lines_dict.get("color") is not None:
                color_line = slash_lines_dict.get("color")
            else:
                color_line = "black"
            if slash_lines_dict.get("color") is not None:
                color_line = slash_lines_dict.get("color")
            else:
                color_line = "black"
            if slash_lines_dict.get("slash_width_inches") is not None:
                slash_width = slash_lines_dict.get("slash_width_inches") * 96
            else:
                slash_width = 0.25

        line_elements = []

        def bezier_eval(p0, c1, c2, p1, t):
            mt = 1 - t
            x = (
                (mt**3) * p0[0]
                + 3 * (mt**2) * t * c1[0]
                + 3 * mt * (t**2) * c2[0]
                + (t**3) * p1[0]
            )
            y = (
                (mt**3) * p0[1]
                + 3 * (mt**2) * t * c1[1]
                + 3 * mt * (t**2) * c2[1]
                + (t**3) * p1[1]
            )
            dx = (
                3 * (mt**2) * (c1[0] - p0[0])
                + 6 * mt * t * (c2[0] - c1[0])
                + 3 * (t**2) * (p1[0] - c2[0])
            )
            dy = (
                3 * (mt**2) * (c1[1] - p0[1])
                + 6 * mt * t * (c2[1] - c1[1])
                + 3 * (t**2) * (p1[1] - c2[1])
            )
            return {"x": x, "y": y, "tangent": math.degrees(math.atan2(dy, dx))}

        def bezier_length(p0, c1, c2, p1, samples=80):
            prev = bezier_eval(p0, c1, c2, p1, 0)
            L = 0.0
            for i in range(1, samples + 1):
                t = i / samples
                pt = bezier_eval(p0, c1, c2, p1, t)
                L += math.hypot(pt["x"] - prev["x"], pt["y"] - prev["y"])
                prev = pt
            return L

        # -------------------------------------------------------------
        # Iterate through Bézier segments
        for i in range(len(points) - 1):
            p0 = (points[i]["x"], points[i]["y"])
            p1 = (points[i + 1]["x"], points[i + 1]["y"])
            t0 = math.radians(points[i].get("tangent", 0))
            t1 = math.radians(points[i + 1].get("tangent", 0))
            d = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
            ctrl_dist = d * 0.5
            c1 = (p0[0] + math.cos(t0) * ctrl_dist, p0[1] + math.sin(t0) * ctrl_dist)
            c2 = (p1[0] - math.cos(t1) * ctrl_dist, p1[1] - math.sin(t1) * ctrl_dist)

            L = bezier_length(p0, c1, c2, p1)
            num_steps = max(1, int(L / step_dist))
            step_dist_actual = L / num_steps  # uniform spacing

            for z in range(num_steps + 1):
                # ------------------------------------------------------------------
                # 1. Evaluate point along Bézier curve
                # ------------------------------------------------------------------
                t_norm = min(1.0, (z * step_dist_actual) / L)
                P = bezier_eval(p0, c1, c2, p1, t_norm)

                # Centerpoint on spline
                center = (P["x"], P["y"])

                # ------------------------------------------------------------------
                # 2. Tangent and hatch angle computation
                # ------------------------------------------------------------------
                # Tangent direction of the spline at this point (radians)
                tangent_angle = math.radians(P["tangent"])

                # LH vs RH determines whether we add or subtract the slant
                if slash_lines_dict.get("direction") == "LH":
                    line_angle = tangent_angle + math.radians(angle_slant)
                else:  # "RH"
                    line_angle = tangent_angle - math.radians(angle_slant)

                # ------------------------------------------------------------------
                # 3. Compute hatch line geometry
                # ------------------------------------------------------------------
                # Shorter lines at steep slant; normalize by cos(slant)
                line_length = stroke_width / math.sin(math.radians(angle_slant))

                # Vector along hatch direction
                dx = math.cos(line_angle) * (line_length / 2)
                dy = math.sin(line_angle) * (line_length / 2)

                # Line endpoints
                x1 = center[0] - dx
                y1 = center[1] - dy
                x2 = center[0] + dx
                y2 = center[1] + dy

                # ------------------------------------------------------------------
                # 4. Append SVG element
                # ------------------------------------------------------------------
                line_elements.append(
                    f'<line x1="{x1:.2f}" y1="{-y1:.2f}" '
                    f'x2="{x2:.2f}" y2="{-y2:.2f}" '
                    f'stroke="{color_line}" stroke-width="{slash_width}" />'
                )

        local_group.extend(line_elements)

    # ---------------------------------------------------------------------
    # --- Main body rendering
    # ---------------------------------------------------------------------
    base_color = appearance_dict.get("base_color", "white")
    outline_color = appearance_dict.get("outline_color")
    path_d = spline_to_path(spline_points)

    # outline path
    stroke_width = stroke_width_inches * 96
    if outline_color:
        local_group.append(
            f'<path d="{path_d}" stroke="{outline_color}" stroke-width="{stroke_width}" '
            f'fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
        )
        stroke_width = stroke_width - 0.5

    # base path
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
        stripe_thickness = stroke_width / num
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

    # --- Slash lines ---
    if appearance_dict.get("slash_lines") is not None:
        slash_lines_dict = appearance_dict.get("slash_lines")
        draw_slash_lines(spline_points, slash_lines_dict)