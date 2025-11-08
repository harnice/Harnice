import math
from time import sleep
from harnice import fileio, state
from harnice.lists import instances_list
from harnice.utils import formboard_utils


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


# ===================== FILE STRUCTURE =====================
def file_structure():
    return {
        "instance_data": {
            "imported_instances": {
                "macro": {
                    artifact_id: {
                        f"{state.partnumber('pn-rev')}-{artifact_id}-master.svg": "segment visualizer svg",
                    }
                }
            }
        }
    }


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
        radius_inches = 1
        radius_px = radius_inches * 96
        svg_groups.append(circle_svg(x_node, y_node, radius_px, "black"))

        node_segment_angles = []
        node_segments = []
        for instance in instances:
            if instance.get("item_type") == "segment":
                if instance.get("node_at_end_a") == node.get("instance_name"):
                    node_segment_angles.append(float(instance.get("absolute_rotation")))
                    node_segments.append(instance)
                elif instance.get("node_at_end_b") == node.get("instance_name"):
                    temp_angle = float(instance.get("absolute_rotation")) + 180
                    if temp_angle > 360:
                        temp_angle -= 360
                    node_segment_angles.append(temp_angle)
                    node_segments.append(instance)

        for seg_angle, seg in zip(node_segment_angles, node_segments):
            seg_name = seg.get("instance_name")

            # ✅ alphabetical instance order for this segment
            component_names_sorted = sorted_segment_contents.get(seg_name, [])
            num_seg_components = len(component_names_sorted)

            for idx, inst_name in enumerate(component_names_sorted, start=1):
                # lookup instance object
                component = next(i for i in instances if i.get("instance_name") == inst_name)

                center_offset_from_count_inches = (
                    idx - (num_seg_components / 2) - 0.5
                ) * segment_spacing_inches

                delta_angle_from_count = (
                    math.asin(center_offset_from_count_inches / radius_inches)
                    * 180
                    / math.pi
                )

                x_circleintersect = x_node + radius_px * math.cos(
                    math.radians(seg_angle + delta_angle_from_count)
                )
                y_circleintersect = y_node + radius_px * math.sin(
                    math.radians(seg_angle + delta_angle_from_count)
                )

                svg_groups.append(
                    circle_svg(x_circleintersect, y_circleintersect, 0.1 * 96, "red")
                )

                # ✅ store using instance_name instead of numeric counters
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
                break
            else:
                another_segment_exists_after = False

    print(instance1.get("instance_name"))
    print(point_chain)
    cleaned_chain = [pt for pt in point_chain if isinstance(pt, dict)]
    svg_groups.append(
        f'<path d="{spline_from_point_chain(cleaned_chain, tangent_scale=0.6)}" '
        f'stroke="blue" fill="none" stroke-width="{0.1*96}"/>'
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
