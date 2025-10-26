import os
import math
from collections import defaultdict
from harnice import fileio
from harnice.utils import flagnote_utils, svg_utils

artifact_mpn = "standard_harnice_formboard"


# =============== PATHS ===============
def path(target_value):
    # artifact_path gets passed in as a global from the caller
    if target_value == "output svg":
        return os.path.join(
            artifact_path, f"{fileio.partnumber('pn-rev')}-{artifact_id}-master.svg"
        )
    if target_value == "show hide":
        return os.path.join(
            artifact_path, f"{fileio.partnumber('pn-rev')}-{artifact_id}-showhide.json"
        )
    if target_value == "flagnotes":
        return os.path.join(artifact_path, f"{artifact_id}-flagnotes")
    else:
        raise KeyError(f"Filename {target_value} not found in {artifact_mpn} file tree")


def update_showhide():
    # === Titleblock Defaults ===
    blank_setup = {"hide_instances": {}, "hide_item_types": {}}

    return blank_setup


def calculate_formboard_location(instance_name, origin):
    instances = fileio.read_tsv("instances list")
    instances_lookup = {row["instance_name"]: row for row in instances}

    chain = []
    current = instance_name

    # === Build chain of parents ===
    while current:
        chain.append(current)
        row = instances_lookup.get(current)
        if not row:
            break
        parent = row.get("parent_csys_instance_name", "").strip()
        if not parent:
            break
        current = parent

    x_pos, y_pos, angle = origin  # unpack origin

    # Walk down the chain (excluding the instance itself)
    for name in reversed(chain):
        row = instances_lookup.get(name, {})

        translate_x = float(row.get("translate_x", 0) or 0)
        translate_y = float(row.get("translate_y", 0) or 0)
        rotate_csys = float(row.get("rotate_csys", 0) or 0)

        # Apply translation in the parent's local coordinates
        rad = math.radians(angle)
        dx = math.cos(rad) * translate_x - math.sin(rad) * translate_y
        dy = math.sin(rad) * translate_x + math.cos(rad) * translate_y

        x_pos += dx
        y_pos += dy
        angle += rotate_csys  # update orientation after translation

    return x_pos, y_pos, angle


# ==========================
fileio.silentremove(path("flagnotes"))
instances = fileio.read_tsv("instances list")
printable_item_types = {"Connector", "Backshell", "Segment", "Flagnote"}

if "Flagnote" in printable_item_types:
    flagnote_utils.make_note_drawings(path("flagnotes"))

rotation = 0  # TODO: FIGURE OUT HOW TO PASS THIS IN SOMEWHERE
if rotation == "":
    raise KeyError(
        f"[ERROR] Rotation '{rotation}' not found in harnice output contents"
    )
origin = [0, 0, rotation]

# Group instances by item_type
grouped_instances = defaultdict(list)
for instance in instances:
    item_type = instance.get("item_type", "").strip()
    if item_type and item_type in printable_item_types:
        grouped_instances[item_type].append(instance)

# Prepare lines for SVG content
content_lines = []
# TODO: fix hide stuff
# formboard = page_setup_contents["formboards"].get(formboard_name, {})
hide_filters = {}  # formboard_utils.get("hide_instances", {})

for item_type, items in grouped_instances.items():
    content_lines.append(f'    <g id="{item_type}" inkscape:label="{item_type}">')
    for instance in items:
        # === Cancel if instance matches any hide filter ===
        should_hide = False
        if not hide_filters == []:
            for filter_conditions in hide_filters.values():
                if all(instance.get(k) == v for k, v in filter_conditions.items()):
                    should_hide = True
                    break
        if should_hide:
            continue

        instance_name = instance.get("instance_name", "")
        if not instance_name:
            continue

        x, y, angle = calculate_formboard_location(instance_name, origin)

        px_x = x * 96
        px_y = y * 96

        if instance.get("item_type") == "Segment":
            angle += origin[2]

        if instance.get("absolute_rotation") != "":
            angle = float(instance.get("absolute_rotation"))

        if instance.get("item_type") == "Segment":
            angle += origin[2]

        svg_px_x = px_x
        svg_px_y = -1 * px_y
        svg_angle = -1 * angle

        if item_type == "Flagnote":
            if instance.get("parent_instance") in ["", None]:
                continue

            # Unpack both positions
            x_note, y_note, flagnote_orientation = calculate_formboard_location(
                instance_name, origin
            )
            x_leader, y_leader, angle_leader = calculate_formboard_location(
                f"{instance_name}.leader", origin
            )

            # Compute offset vector in SVG coordinates
            leader_dx = (x_leader - x_note) * 96
            leader_dy = (
                y_leader - y_note
            ) * -96  # change polarity of y offset (svg coordinate transform)

            # Arrowhead geometry
            arrow_length = 8  # length of the arrowhead in pixels
            arrow_width = 6  # width of the arrowhead in pixels
            line_len = math.hypot(leader_dx, leader_dy)
            if line_len == 0:
                line_len = 1  # prevent divide-by-zero
            ux = leader_dx / line_len
            uy = leader_dy / line_len

            # Tip of arrow
            tip_x = leader_dx * scale
            tip_y = leader_dy * scale

            # Base corners of arrowhead
            left_x = tip_x - arrow_length * ux + arrow_width * uy / 2
            left_y = tip_y - arrow_length * uy - arrow_width * ux / 2
            right_x = tip_x - arrow_length * ux - arrow_width * uy / 2
            right_y = tip_y - arrow_length * uy + arrow_width * ux / 2

            content_lines.append(
                f'      <g id="{instance_name}-translate" transform="translate({svg_px_x},{svg_px_y})">'
            )
            content_lines.append(
                f'        <line x1="0" y1="0" x2="{tip_x}" y2="{tip_y}" stroke="black" stroke-width="1"/>'
            )
            content_lines.append(
                f'        <polygon points="{tip_x},{tip_y} {left_x},{left_y} {right_x},{right_y}" fill="black"/>'
            )
            content_lines.append(
                f'        <g id="{instance_name}-rotate" transform="rotate({-1 * angle})">'
            )
            content_lines.append(
                f'          <g id="{instance_name}-scale" transform="scale({1 / scale})">'
            )
            content_lines.append(
                f'            <g id="{instance_name}-contents-start" inkscape:label="{instance_name}-contents-start">'
            )
            content_lines.append(f"            </g>")
            content_lines.append(
                f'            <g id="{instance_name}-contents-end" inkscape:label="{instance_name}-contents-end"></g>'
            )
            content_lines.append(f"          </g>")
            content_lines.append(f"        </g>")
            content_lines.append(f"      </g>")
        else:
            content_lines.append(
                f'      <g id="{instance_name}-contents-start" inkscape:label="{instance_name}-contents-start" transform="translate({svg_px_x},{svg_px_y}) rotate({-1 * angle})">'
            )
            content_lines.append("      </g>")
            content_lines.append(
                f'      <g id="{instance_name}-contents-end" inkscape:label="{instance_name}-contents-end"></g>'
            )

    content_lines.append("    </g>")

# Write full SVG
with open(path("output svg"), "w") as f:
    f.write('<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n')
    f.write(
        '<svg xmlns="http://www.w3.org/2000/svg" '
        'xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" '
        'version="1.1" width="1000" height="1000">\n'
    )
    f.write(f'  <g id="{artifact_id}-contents-start">\n')
    f.write(f'    <g id="{artifact_id}-scale_group" transform="scale({scale})">\n')
    f.writelines(line + "\n" for line in content_lines)
    f.write("    </g>\n")
    f.write("  </g>\n")
    f.write(f'  <g id="{artifact_id}-contents-end">\n')
    f.write("  </g>\n")
    f.write("</svg>\n")

# now that the SVG has been written, copy the connector content in:
for instance in instances:
    item_type = instance.get("item_type", "").strip()
    if item_type and item_type in printable_item_types:
        # === Cancel if instance matches any hide filter ===
        should_hide = False
        if not hide_filters == []:
            for filter_conditions in hide_filters.values():
                if all(instance.get(k) == v for k, v in filter_conditions.items()):
                    should_hide = True
                    break
        if should_hide:
            continue

        #locally generated instances are stored here
        if instance.get("item_type").strip().lower() in [
            "segment"
        ]:
            instance_data_dir = os.path.join(fileio.dirpath("generated_instances_do_not_edit"), instance.get("instance_name"), f"{instance.get('instance_name')}-drawing.svg")
        #imported instances are here
        else:
            instance_data_dir = os.path.join(fileio.dirpath("imported_instances"), instance.get("item_type"), instance.get("instance_name"), f"{instance.get('instance_name')}-drawing.svg")

        svg_utils.find_and_replace_svg_group(
            path("output svg"),
            instance_data_dir,
            instance.get("instance_name"),
            instance.get("instance_name"),
        )
