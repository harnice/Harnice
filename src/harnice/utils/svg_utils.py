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
    Draws a spline path with appearance styling.
    Supports left-hand (LH) and right-hand (RH) twisted wire hatching
    with uniform line density and consistent diagonal direction.
    """

    if not appearance_dict:
        appearance_dict = {"base_color": "black"}

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
    def draw_twist_lines(points, color_line, step_dist, direction):
        line_elements = []
        offset_dist = stroke_width / 2
        angle_slant = 45  # degrees relative to tangent

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
                t_norm = min(1.0, (z * step_dist_actual) / L)
                P = bezier_eval(p0, c1, c2, p1, t_norm)

                # Tangent and normal vectors
                tx = math.cos(math.radians(P["tangent"]))
                ty = math.sin(math.radians(P["tangent"]))
                nx = -ty
                ny = tx

                # --- Compute slanted hatch direction ---
                # Rotate the normal by ±angle_slant relative to tangent
                rot = math.radians(angle_slant * direction)
                sx = tx * math.sin(rot) + nx * math.cos(rot)
                sy = ty * math.sin(rot) + ny * math.cos(rot)

                # Hatch line endpoints (crosses through the wire)
                x1 = P["x"] - sx * offset_dist
                y1 = P["y"] - sy * offset_dist
                x2 = P["x"] + sx * offset_dist
                y2 = P["y"] + sy * offset_dist

                line_elements.append(
                    f'<line x1="{x1:.2f}" y1="{-y1:.2f}" '
                    f'x2="{x2:.2f}" y2="{-y2:.2f}" '
                    f'stroke="{color_line}" stroke-width="0.5" '
                    f'stroke-opacity="0.9" />'
                )

        local_group.extend(line_elements)

    # ---------------------------------------------------------------------
    # --- Main body rendering
    # ---------------------------------------------------------------------
    base_color = appearance_dict.get("base_color", "black")
    outline_color = appearance_dict.get("outline_color")
    path_d = spline_to_path(spline_points)

    # outline path
    if outline_color:
        local_group.append(
            f'<path d="{path_d}" stroke="{outline_color}" stroke-width="{stroke_width + 1.5}" '
            f'fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
        )

    # base path
    local_group.append(
        f'<path d="{path_d}" stroke="{base_color}" stroke-width="{stroke_width}" '
        f'fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
    )

    # --- Twisted wires ---
    twist = appearance_dict.get("twisted")
    if twist in ("RH", "LH"):
        direction = 1 if twist == "LH" else -1
        draw_twist_lines(spline_points, "black", stroke_width * 2.0, direction)
