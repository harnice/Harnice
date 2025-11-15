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

import math
import uuid


def draw_styled_path(spline_points, stroke_width, appearance_dict, local_group):
    """
    Draws a spline path with appearance styling.
    Uses parametric Bézier sampling for accurate hatch lines and dot markers.
    """

    if not appearance_dict:
        appearance_dict = {"base_color": "black"}

    # ---------------------------------------------------------------------
    # --- helper: cubic Bézier parametric evaluation
    # ---------------------------------------------------------------------
    def bezier_coeffs(p0, c1, c2, p1):
        """Return lambda x(t), y(t), dx/dt, dy/dt for cubic Bézier 0 ≤ t ≤ 1."""
        def poly(a0, a1, a2, a3):
            return (
                lambda t: ((1 - t) ** 3) * a0
                + 3 * ((1 - t) ** 2) * t * a1
                + 3 * (1 - t) * (t ** 2) * a2
                + (t ** 3) * a3
            )

        def dpoly(a0, a1, a2, a3):
            return (
                lambda t: 3 * ((1 - t) ** 2) * (a1 - a0)
                + 6 * (1 - t) * t * (a2 - a1)
                + 3 * (t ** 2) * (a3 - a2)
            )

        return (
            poly(p0[0], c1[0], c2[0], p1[0]),
            poly(p0[1], c1[1], c2[1], p1[1]),
            dpoly(p0[0], c1[0], c2[0], p1[0]),
            dpoly(p0[1], c1[1], c2[1], p1[1]),
        )

    # ---------------------------------------------------------------------
    # --- helper: approximate arc length and sample equal-spacing points
    # ---------------------------------------------------------------------
    def sample_bezier_equal_arc(p0, c1, c2, p1, step=2.0):
        """Return list of (x, y, tangent_deg) points sampled by equal arc length."""
        x_t, y_t, dx_t, dy_t = bezier_coeffs(p0, c1, c2, p1)
        n = 80
        pts = [(x_t(i / n), y_t(i / n)) for i in range(n + 1)]
        dists = [0.0]
        for i in range(1, len(pts)):
            seg = math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1])
            dists.append(dists[-1] + seg)
        total_len = dists[-1]
        if total_len < 1e-6:
            return [p0, p1]

        n_steps = max(2, int(total_len // step))
        targets = [i * total_len / n_steps for i in range(n_steps + 1)]

        sampled = []
        for tlen in targets:
            for i in range(1, len(dists)):
                if dists[i] >= tlen:
                    frac = (tlen - dists[i - 1]) / (dists[i] - dists[i - 1])
                    t = ((i - 1) + frac) / n
                    x, y = x_t(t), y_t(t)
                    dx, dy = dx_t(t), dy_t(t)
                    tangent = math.degrees(math.atan2(dy, dx))
                    sampled.append({"x": x, "y": y, "tangent": tangent})
                    break
        return sampled

    # ---------------------------------------------------------------------
    # --- helper: spline_to_path
    # ---------------------------------------------------------------------
    def spline_to_path(points):
        if len(points) < 2:
            return ""
        path = f"M {points[0]['x']:.3f},{-points[0]['y']:.3f}"
        for i in range(len(points) - 1):
            p0, p1 = points[i], points[i + 1]
            t0, t1 = math.radians(p0.get("tangent", 0)), math.radians(p1.get("tangent", 0))
            d = math.hypot(p1["x"] - p0["x"], p1["y"] - p0["y"])
            ctrl_dist = d * 0.5
            c1x = p0["x"] + math.cos(t0) * ctrl_dist
            c1y = p0["y"] + math.sin(t0) * ctrl_dist
            c2x = p1["x"] - math.cos(t1) * ctrl_dist
            c2y = p1["y"] - math.sin(t1) * ctrl_dist
            path += f" C {c1x:.3f},{-c1y:.3f} {c2x:.3f},{-c2y:.3f} {p1['x']:.3f},{-p1['y']:.3f}"
        return path

    # ---------------------------------------------------------------------
    # --- helper: hatch lines using parametrization
    # ---------------------------------------------------------------------
    def hatch_lines_parametric(points, hatch_angle, stroke_width, color="black", clip_id=None, path_d=None):
        """Use parametric sampling for evenly spaced hatch lines."""
        hatch_elements = []
        for i in range(len(points) - 1):
            p0 = (points[i]["x"], points[i]["y"])
            p1 = (points[i + 1]["x"], points[i + 1]["y"])
            t0 = math.radians(points[i].get("tangent", 0))
            t1 = math.radians(points[i + 1].get("tangent", 0))
            d = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
            ctrl_dist = d * 0.5
            c1 = (p0[0] + math.cos(t0) * ctrl_dist, p0[1] + math.sin(t0) * ctrl_dist)
            c2 = (p1[0] - math.cos(t1) * ctrl_dist, p1[1] - math.sin(t1) * ctrl_dist)

            sampled = sample_bezier_equal_arc(p0, c1, c2, p1, step=stroke_width * 1.5)

            theta = math.radians(hatch_angle)
            for pt in sampled:
                tdir = math.radians(pt["tangent"])
                nx, ny = -math.sin(tdir), math.cos(tdir)
                hx = nx * math.cos(theta) - ny * math.sin(theta)
                hy = nx * math.sin(theta) + ny * math.cos(theta)
                length = stroke_width / abs(math.cos(theta))
                hx1, hy1 = pt["x"] - hx * length / 2, pt["y"] - hy * length / 2
                hx2, hy2 = pt["x"] + hx * length / 2, pt["y"] + hy * length / 2
                hatch_elements.append(
                    f'<line x1="{hx1:.2f}" y1="{-hy1:.2f}" '
                    f'x2="{hx2:.2f}" y2="{-hy2:.2f}" '
                    f'stroke="{color}" stroke-width="0.35" stroke-opacity="0.9"/>'
                )

        if clip_id and path_d:
            local_group.append(
                f'<clipPath id="{clip_id}">'
                f'<path d="{path_d}" stroke="black" stroke-width="{stroke_width}" '
                f'stroke-linecap="round" stroke-linejoin="round" fill="none"/>'
                f'</clipPath>'
            )
            local_group.append(f'<g clip-path="url(#{clip_id})">' + "\n".join(hatch_elements) + "</g>")
        else:
            local_group.extend(hatch_elements)

    # ---------------------------------------------------------------------
    # --- helper: draw dots along the spline
    # ---------------------------------------------------------------------
    # ---------------------------------------------------------------------
    # --- helper: draw paired dots offset from the spline centerline
    # ---------------------------------------------------------------------
    def draw_sample_dots(points, color_center="red", color_side="blue", radius=0.6):
        """Draw two dots offset from the tangent line (left/right of center)."""
        dot_elements = []
        offset_dist = stroke_width / 2

        for i in range(len(points) - 1):
            p0 = (points[i]["x"], points[i]["y"])
            p1 = (points[i + 1]["x"], points[i + 1]["y"])
            t0 = math.radians(points[i].get("tangent", 0))
            t1 = math.radians(points[i + 1].get("tangent", 0))
            d = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
            ctrl_dist = d * 0.5
            c1 = (p0[0] + math.cos(t0) * ctrl_dist, p0[1] + math.sin(t0) * ctrl_dist)
            c2 = (p1[0] - math.cos(t1) * ctrl_dist, p1[1] - math.sin(t1) * ctrl_dist)

            # sample points at equal arc-length intervals
            sampled = sample_bezier_equal_arc(p0, c1, c2, p1, step=stroke_width * 1.5)

            for pt in sampled:
                # tangent + normal
                theta = math.radians(pt["tangent"])
                nx, ny = -math.sin(theta), math.cos(theta)

                # left/right offset points
                px_left  = pt["x"] + nx * offset_dist
                py_left  = pt["y"] + ny * offset_dist
                px_right = pt["x"] - nx * offset_dist
                py_right = pt["y"] - ny * offset_dist

                # draw left and right dots
                dot_elements.append(
                    f'<circle cx="{px_left:.2f}" cy="{-py_left:.2f}" '
                    f'r="{radius:.2f}" fill="{color_side}" />'
                )
                dot_elements.append(
                    f'<circle cx="{px_right:.2f}" cy="{-py_right:.2f}" '
                    f'r="{radius:.2f}" fill="{color_side}" />'
                )

                # optional center marker for debugging
                dot_elements.append(
                    f'<circle cx="{pt["x"]:.2f}" cy="{-pt["y"]:.2f}" '
                    f'r="{radius * 0.6:.2f}" fill="{color_center}" />'
                )

        local_group.extend(dot_elements)

    # ---------------------------------------------------------------------
    # --- Main body rendering
    # ---------------------------------------------------------------------
    base_color = appearance_dict.get("base_color", "black")
    outline_color = appearance_dict.get("outline_color")
    path_d = spline_to_path(spline_points)
    clip_id = f"clip_{uuid.uuid4().hex[:8]}"

    if outline_color:
        local_group.append(
            f'<path d="{path_d}" stroke="{outline_color}" stroke-width="{stroke_width + 1.5}" '
            f'fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
        )

    local_group.append(
        f'<path d="{path_d}" stroke="{base_color}" stroke-width="{stroke_width}" '
        f'fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
    )

    # --- Twisted wires (parametric hatch) ---
    twist = appearance_dict.get("twisted")
    if twist == "RH":
        hatch_lines_parametric(spline_points, 70, stroke_width, color=base_color, clip_id=clip_id, path_d=path_d)
    elif twist == "LH":
        hatch_lines_parametric(spline_points, -70, stroke_width, color=base_color, clip_id=clip_id, path_d=path_d)

    # --- Dot visualization ---
    draw_sample_dots(spline_points, radius=0.6)
