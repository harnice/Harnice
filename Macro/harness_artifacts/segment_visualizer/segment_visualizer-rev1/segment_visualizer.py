import math
from harnice import fileio, state
from harnice.lists import instances_list
from harnice.utils import formboard_utils


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
    raise ValueError("item_type is required: which item types are you trying to visualize?")

if scale is None:
    raise ValueError("scale is required")


points_to_pass_through = {}

instances = fileio.read_tsv("instances list")
for node in instances:
    if node.get("item_type") == "node":
        #print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        #print(f"{node.get("instance_name")}")
        x_px, y_px, seg_angle = formboard_utils.calculate_location(node.get("instance_name"), origin)
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
                        temp_angle = temp_angle - 360
                    node_segment_angles.append(temp_angle)
                    node_segments.append(instance)
        
        for seg_angle, seg in zip(node_segment_angles, node_segments):
            #print(f"    {seg.get("instance_name")}: {seg_angle}")
            components_of_segment = []
            for instance in instances:
                if instance.get("item_type") == item_type:
                    if instance.get("segment_group") == seg.get("instance_name"):
                        components_of_segment.append(instance)
            num_seg_components = len(components_of_segment)
            seg_counter = 1
            for component in components_of_segment:
                #print(f"        {component.get("instance_name")}")
                center_offset_from_count_inches = (seg_counter - (num_seg_components / 2) - 0.5) * segment_spacing_inches
                delta_angle_from_count = math.asin(center_offset_from_count_inches / radius_inches) * 180 / math.pi
                #print(f"            {center_offset_from_count_inches}")
                #print(f"            {delta_angle_from_count}")
                x_circleintersect = x_node + radius_px * math.cos(math.radians(seg_angle + delta_angle_from_count))
                y_circleintersect = y_node + radius_px * math.sin(math.radians(seg_angle + delta_angle_from_count))
                svg_groups.append(circle_svg(x_circleintersect, y_circleintersect, 0.1*96, "red"))
                node_name = node.get("instance_name")
                seg_name = seg.get("instance_name")
                count_key = str(seg_counter)

                # Ensure nested structure exists
                if node_name not in points_to_pass_through:
                    points_to_pass_through[node_name] = {}
                if seg_name not in points_to_pass_through[node_name]:
                    points_to_pass_through[node_name][seg_name] = {}
                if count_key not in points_to_pass_through[node_name][seg_name]:
                    points_to_pass_through[node_name][seg_name][count_key] = {}

                points_to_pass_through[node_name][seg_name][count_key]["x"] = x_circleintersect
                points_to_pass_through[node_name][seg_name][count_key]["y"] = y_circleintersect
                seg_counter = seg_counter + 1

#print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
print_nested(points_to_pass_through)


# === Wrap with contents-start / contents-end, scale inside contents-start ===
svg_output = (
    '<svg xmlns="http://www.w3.org/2000/svg" stroke-linecap="round" stroke-linejoin="round">\n'
    f'  <g id="{artifact_id}-contents-start">\n'
    f'    <g id="scale" transform="scale({scale})">\n'
    + "\n".join(svg_groups) +
    "\n    </g>\n"
    f'  </g>\n'
    f'  <g id="{artifact_id}-contents-end"/>\n'
    "</svg>\n"
)


# =============== WRITE OUTPUT FILE ===============
out_path = fileio.path("segment visualizer svg", structure_dict=file_structure())
with open(out_path, "w", encoding="utf-8") as f:
    f.write(svg_output)
