import math
from collections import defaultdict
import os
from harnice import fileio, state
from harnice.lists import instances_list
from harnice.utils import formboard_utils

print_circles_and_dots = False

try:
    stroke_color = wire_color
except:
    #TODO: pull in info from conductor attributes
    stroke_color = "black"

segment_spacing_inches_scaled = segment_spacing_inches / scale

def label_svg(
    x, y, angle, text,
    text_color="black",
    background_color="white",
    outline="black",
    font_size=6,
    font_family="Arial, Helvetica, sans-serif;",
    font_weight="normal",
):
    font_size = font_size / scale
    """
    Returns SVG snippet for a centered label (text + background rectangle).
    Uses formatting style consistent with your existing <text> usage.
    """

    # Flip y because SVG coordinate system is positive-down
    y_svg = -y

    if angle > 90 and angle < 270:
        angle = angle + 180

    if angle > 360:
        angle -= 360

    # Background box sizing
    char_width = font_size * 0.6
    text_width = len(text) * char_width
    text_height = font_size
    padding = 4
    width = text_width + padding * 2
    height = text_height + padding * 2

    # Centered rectangle offsets
    rect_x = -width / 2
    rect_y = -height / 2

    return f"""
<g transform="translate({x:.3f},{y_svg:.3f}) rotate({-angle:.3f})">
  <rect x="{rect_x:.3f}" y="{rect_y:.3f}"
        width="{width:.3f}" height="{height:.3f}"
        fill="{background_color}" stroke="{outline}" stroke-width="0.8"/>
  <text x="0" y="0" text-anchor="middle"
        style="fill:{text_color};dominant-baseline:middle;
               font-weight:{font_weight};font-family:{font_family};
               font-size:{font_size}px">{text}</text>
</g>
""".strip()



def print_nested(data, indent=0):
    prefix = "    " * indent
    if isinstance(data, dict):
        for key, value in data.items():
            print(f"{prefix}{key}:")
            print_nested(value, indent + 1)
    elif isinstance(data, list):
        print(prefix + ", ".join(str(v) for v in data))
    else:
        print(prefix + str(data))



def average_coords(data):
    sums = defaultdict(lambda: {"x": 0.0, "y": 0.0, "count": 0})

    for _lvl1, lvl2 in data.items():
        for _lvl2, lvl3 in lvl2.items():
            for key, coords in lvl3.items():
                sums[key]["x"] += coords["x"]
                sums[key]["y"] += coords["y"]
                sums[key]["count"] += 1

    # convert accumulated sums into averages
    averages = {}
    for key, v in sums.items():
        averages[key] = {
            "x": v["x"] / v["count"],
            "y": v["y"] / v["count"],
        }
        averages[key]["angle"] = float(instances_list.attribute_of(instances_list.attribute_of(key, "segment_group"), "absolute_rotation"))
        averages[key]["text"] = instances_list.attribute_of(key, "parent_instance") #TODO: change to print name, but that currently shows color/appearance
    return averages


def spline_from_point_chain(chain, tangent_scale=0.5):
    """
    Returns an SVG path string using cubic Beziers,
    matching point positions and tangent angles.
    tangent_scale controls how 'curvy' the spline is.
    """

    if len(chain) < 2:
        return ""

    def deg_to_vec(deg):
        rad = math.radians(deg)
        return math.cos(rad), math.sin(rad)

    # Move to the first point
    p0 = chain[0]
    path = f'M {p0["x"]:.3f},{-p0["y"]:.3f}'  # flip y for SVG

    for i in range(len(chain) - 1):
        p0 = chain[i]
        p1 = chain[i + 1]

        # tangent directions
        vx0, vy0 = deg_to_vec(p0["tangent"])
        vx1, vy1 = deg_to_vec(p1["tangent"])

        # control point distances
        # proportional to distance between points
        dx = p1["x"] - p0["x"]
        dy = p1["y"] - p0["y"]
        dist = math.sqrt(dx*dx + dy*dy)

        c0x = p0["x"] + vx0 * dist * tangent_scale
        c0y = p0["y"] + vy0 * dist * tangent_scale
        c1x = p1["x"] - vx1 * dist * tangent_scale
        c1y = p1["y"] - vy1 * dist * tangent_scale

        # Add cubic curve
        path += (
            f' C {c0x:.3f},{-c0y:.3f} '
            f'{c1x:.3f},{-c1y:.3f} '
            f'{p1["x"]:.3f},{-p1["y"]:.3f}'
        )

    return path



def circle_svg(x, y, r, color):
    # Flip Y because formboard coordinate system is positive-up
    y_svg = -y
    return f'<circle cx="{x:.3f}" cy="{y_svg:.3f}" r="{r:.3f}" fill="{color}" />'


# ===================== FILE STRUCTURE =====================
def file_structure():
    return {
        "instance_data": {
            "imported_instances": {
                "macro": {
                    artifact_id: {
                        f"{state.partnumber('pn-rev')}-{artifact_id}-master.svg": "segment visualizer svg",
                        f"{artifact_id}-imported-instances": {},
                    }
                }
            }
        }
    }

os.makedirs(fileio.dirpath(f"{artifact_id}-imported-instances", structure_dict=file_structure()), exist_ok=True)


# =============== BUILD SVG CONTENT ===============

instances = fileio.read_tsv("instances list")
svg_groups = []

try:
    if not rotation:
        rotation = 0
except NameError:
    rotation = 0
origin = [0, 0, rotation]

if item_type is None:
    raise ValueError(
        "item_type is required: which item types are you trying to visualize?"
    )

if scale is None:
    raise ValueError("scale is required")


points_to_pass_through = {}

# ================================
# collect instances
# ================================
instances = fileio.read_tsv("instances list")

# ================================
# sort item_type instances alphabetically inside each segment
# ================================
sorted_segment_contents = {
    seg.get("instance_name"): []
    for seg in instances
    if seg.get("item_type") == "segment"
}

for inst in instances:
    if inst.get("item_type") == item_type:
        segment_name = inst.get("segment_group")
        if segment_name in sorted_segment_contents:
            sorted_segment_contents[segment_name].append(inst.get("instance_name"))

for seg_name in sorted_segment_contents:
    sorted_segment_contents[seg_name].sort()


# ================================
# collect points to pass through
# ================================
for node in instances:
    if node.get("item_type") == "node":
        x_px, y_px, seg_angle = formboard_utils.calculate_location(
            node.get("instance_name"), origin
        )
        x_node, y_node = x_px * 96, y_px * 96

        node_segment_angles = []
        node_segments = []
        flip_sort = {}
        for instance in instances:
            if instance.get("item_type") == "segment":
                if instance.get("node_at_end_a") == node.get("instance_name"):
                    node_segment_angles.append(float(instance.get("absolute_rotation")))
                    node_segments.append(instance)
                    flip_sort[instance.get("instance_name")] = False
                elif instance.get("node_at_end_b") == node.get("instance_name"):
                    temp_angle = float(instance.get("absolute_rotation")) + 180
                    if temp_angle > 360:
                        temp_angle -= 360
                    node_segment_angles.append(temp_angle)
                    node_segments.append(instance)
                    flip_sort[instance.get("instance_name")] = True

        components_in_node = 0
        components_seen = []
        for instance in instances:
            if instance.get("item_type") == item_type:
                segment_candidate = instance.get("segment_group")
                if instance.get("parent_instance") in components_seen:
                    continue
                if instances_list.attribute_of(segment_candidate, "node_at_end_a") == node.get("instance_name") or instances_list.attribute_of(segment_candidate, "node_at_end_b") == node.get("instance_name"):
                    components_seen.append(instance.get("parent_instance"))
                    components_in_node += 1

        node_radius_inches = 1 + math.pow(components_in_node, 1.5) * segment_spacing_inches_scaled / 4 #1.5th power because vibes
        node_radius_px = node_radius_inches * 96
        if print_circles_and_dots:
            svg_groups.append(circle_svg(x_node, y_node, node_radius_px, "gray"))

        for seg_angle, seg in zip(node_segment_angles, node_segments):
            seg_name = seg.get("instance_name")

            if flip_sort.get(seg_name):
                component_names_sorted = sorted_segment_contents.get(seg_name, [])
            else:
                component_names_sorted = sorted_segment_contents.get(seg_name, [])[::-1]
            num_seg_components = len(component_names_sorted)

            for idx, inst_name in enumerate(component_names_sorted, start=1):
                # lookup instance object
                component = next(i for i in instances if i.get("instance_name") == inst_name)

                center_offset_from_count_inches = (
                    idx - (num_seg_components / 2) - 0.5
                ) * segment_spacing_inches_scaled

                try:
                    delta_angle_from_count = (
                        math.asin(center_offset_from_count_inches / node_radius_inches)
                        * 180
                        / math.pi
                    )
                except ValueError:
                    raise ValueError("Node radius is too small to fit all the necessary segments onto it. Try decreasing the segment spacing.")

                x_circleintersect = x_node + node_radius_px * math.cos(
                    math.radians(seg_angle + delta_angle_from_count)
                )
                y_circleintersect = y_node + node_radius_px * math.sin(
                    math.radians(seg_angle + delta_angle_from_count)
                )

                if print_circles_and_dots:
                    svg_groups.append(
                        circle_svg(x_circleintersect, y_circleintersect, 0.1 * 96, "red")
                    )

                node_name = node.get("instance_name")
                if node_name not in points_to_pass_through:
                    points_to_pass_through[node_name] = {}
                if seg_name not in points_to_pass_through[node_name]:
                    points_to_pass_through[node_name][seg_name] = {}

                points_to_pass_through[node_name][seg_name][inst_name] = {
                    "x": x_circleintersect,
                    "y": y_circleintersect,
                }

unique_parents = []
instances = fileio.read_tsv("instances list")
for instance1 in instances:
    if instance1.get("item_type") != item_type:
        continue
    if instance1.get("parent_instance") in unique_parents:
        continue
    unique_parents.append(instance1.get("parent_instance"))

    point_chain = []
    segment_order = 0
    another_segment_exists_after = True

    while another_segment_exists_after:
        segment_order += 1
        ab_lookup_key = f"{segment_order}-ab"
        ba_lookup_key = f"{segment_order}-ba"

        found_this_step = False

        for instance2 in instances:
            if instance2.get("item_type") != item_type:
                continue
            if instance2.get("parent_instance") != instance1.get("parent_instance"):
                continue

            if instance2.get("segment_order") == ab_lookup_key:
                tangent = float(instances_list.attribute_of(instance2.get("segment_group"), "absolute_rotation"))
                point_chain.append({
                    "x": points_to_pass_through[instances_list.attribute_of(instance2.get("segment_group"), "node_at_end_a")][instance2.get("segment_group")][instance2.get("instance_name")]["x"],
                    "y": points_to_pass_through[instances_list.attribute_of(instance2.get("segment_group"), "node_at_end_a")][instance2.get("segment_group")][instance2.get("instance_name")]["y"],
                    "tangent": tangent,
                })
                point_chain.append({
                    "x": points_to_pass_through[instances_list.attribute_of(instance2.get("segment_group"), "node_at_end_b")][instance2.get("segment_group")][instance2.get("instance_name")]["x"],
                    "y": points_to_pass_through[instances_list.attribute_of(instance2.get("segment_group"), "node_at_end_b")][instance2.get("segment_group")][instance2.get("instance_name")]["y"],
                    "tangent": tangent,
                })
                found_this_step = True
                break

            elif instance2.get("segment_order") == ba_lookup_key:
                tangent = float(instances_list.attribute_of(instance2.get("segment_group"), "absolute_rotation")) + 180
                if tangent > 360:
                    tangent -= 360
                point_chain.append({
                    "x": points_to_pass_through[instances_list.attribute_of(instance2.get("segment_group"), "node_at_end_b")][instance2.get("segment_group")][instance2.get("instance_name")]["x"],
                    "y": points_to_pass_through[instances_list.attribute_of(instance2.get("segment_group"), "node_at_end_b")][instance2.get("segment_group")][instance2.get("instance_name")]["y"],
                    "tangent": tangent,
                })
                point_chain.append({
                    "x": points_to_pass_through[instances_list.attribute_of(instance2.get("segment_group"), "node_at_end_a")][instance2.get("segment_group")][instance2.get("instance_name")]["x"],
                    "y": points_to_pass_through[instances_list.attribute_of(instance2.get("segment_group"), "node_at_end_a")][instance2.get("segment_group")][instance2.get("instance_name")]["y"],
                    "tangent": tangent,
                })
                found_this_step = True
                break

        if not found_this_step:
            another_segment_exists_after = False

    cleaned_chain = [pt for pt in point_chain if isinstance(pt, dict)]
    svg_groups.append(
        f'<path d="{spline_from_point_chain(cleaned_chain)}" '
        f'stroke="black" fill="none" stroke-width="{0.1*96}"/>'
    )
    svg_groups.append(
        f'<path d="{spline_from_point_chain(cleaned_chain)}" '
        f'stroke="{stroke_color}" fill="none" stroke-width="{0.05*96}"/>'
    )
    for order in [0, -1]:
        if order == 0:
            text = instances_list.attribute_of(instance1.get("parent_instance"),"node_at_end_a")
        else:
            text = instances_list.attribute_of(instance1.get("parent_instance"),"node_at_end_b")
        svg_groups.append(
            label_svg(
                cleaned_chain[order].get("x"),
                cleaned_chain[order].get("y"),
                cleaned_chain[order].get("tangent"),
                text,
                text_color = "white",
                background_color = "black"
            )
        )

for key, value in average_coords(points_to_pass_through).items():
    if print_circles_and_dots:
        svg_groups.append(circle_svg(value.get("x"), value.get("y"), 0.1 * 96, "green"))
    svg_groups.append(
        label_svg(
            value.get("x"), 
            value.get("y"), 
            value.get("angle"),
            value.get("text"), 
            text_color="black",
            background_color="white",
            outline="black"
        )
    )

# === Wrap with contents-start / contents-end, scale inside contents-start ===
svg_output = (
    '<svg xmlns="http://www.w3.org/2000/svg" stroke-linecap="round" stroke-linejoin="round">\n'
    f'  <g id="{artifact_id}-contents-start">\n'
    f'    <g id="scale" transform="scale({scale})">\n'
    + "\n".join(svg_groups)
    + "\n    </g>\n"
    f"  </g>\n"
    f'  <g id="{artifact_id}-contents-end"/>\n'
    "</svg>\n"
)


# =============== WRITE OUTPUT FILE ===============
out_path = fileio.path("segment visualizer svg", structure_dict=file_structure())
with open(out_path, "w", encoding="utf-8") as f:
    f.write(svg_output)
