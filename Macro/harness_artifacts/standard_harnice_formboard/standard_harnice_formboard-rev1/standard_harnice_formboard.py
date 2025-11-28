import math
import re
import os
from collections import defaultdict
from harnice import fileio, state
from harnice.utils import library_utils, formboard_utils, svg_utils, feature_tree_utils

artifact_mpn = "standard_harnice_formboard"

"""
Args:
artifact_id : "unique identifier for this instance of the macro (drawing-1)"
scale : scale factor for the drawing
rotation : rotation of the drawing in degrees=
"""

# ==================================================================================================
#               PATHS
# ==================================================================================================
def macro_file_structure(instance_name=None, item_type=None):
    return {
        f"{state.partnumber('pn-rev')}-{artifact_id}-master.svg": "output svg",
    }


if base_directory is None:  # path between cwd and the file structure for this macro
    base_directory = os.path.join("instance_data", "macro", artifact_id)


def path(target_value):
    return fileio.path(
        target_value,
        structure_dict=macro_file_structure(),
        base_directory=base_directory,
    )


def dirpath(target_value):
    # target_value = None will return the root of this macro
    return fileio.dirpath(
        target_value,
        structure_dict=macro_file_structure(),
        base_directory=base_directory,
    )

# ==================================================================================================
#               ARGUMENTS AND GLOBAL SETTINGS
# ==================================================================================================
printable_item_types = {
    "connector",
    "backshell",
    "segment",
    "flagnote",
} 

try:
    if additional_instances:
        for instance in additional_instances:
            input_instances.append(instance)
except NameError:
    pass

# ==================================================================================================
#               HELPER FUNCTIONS
# ==================================================================================================
def make_new_flagnote_drawing(instance, location):
    if instance.get("item_type") != "flagnote":
        raise ValueError(
            f"you just tried to make a flagnote drawing without specifying flagnote type by 'mpn' field on '{instance.get("instance_name")}'"
        )

    # === Pull drawing into this macro ===
    library_utils.pull(instance, destination_directory=location)
    flagnote_drawing_path = os.path.join(
        location, f"{instance.get("instance_name")}-drawing.svg"
    )

    # === Perform text replacement on known drawing path ===
    with open(flagnote_drawing_path, "r", encoding="utf-8") as f:
        svg = f.read()

    svg = re.sub(r">flagnote-text<", f">{instance.get('print_name')}<", svg)

    with open(flagnote_drawing_path, "w", encoding="utf-8") as f:
        f.write(svg)


def make_new_segment_drawing(instance, location):
    if instance.get("item_type") != "segment":
        raise ValueError(
            f"you just tried to make a segment drawing out of a non-segment instance '{instance.get("instance_name")}'"
        )

    feature_tree_utils.run_macro(
        "basic_segment_generator",
        "harness_artifacts",
        "https://github.com/harnice/harnice-library-public",
        artifact_id=f"{artifact_id}-{instance.get("instance_name")}",
        instance=instance,
        base_directory=location,
    )

# ==================================================================================================
#               MAIN RUNTIME LOGIC
# ==================================================================================================
# Group instances by item_type
grouped_instances = defaultdict(list)
for instance in input_instances:
    item_type = instance.get("item_type", "").strip()
    if item_type in printable_item_types:
        grouped_instances[item_type].append(instance)

# Prepare lines for SVG content
content_lines = []
printable_instances = set()
flagnote_position_counter = {}

# ==================================================================================================
# Step through each item_type and add relevant group backbone content to the SVG
for item_type, items in grouped_instances.items():
    content_lines.append(f'    <g id="{item_type}" inkscape:label="{item_type}">')
    for instance in items:
        if instance.get("item_type") not in printable_item_types:
            continue

        instance_name = instance.get("instance_name")
        printable_instances.add(instance_name)
        x, y, angle = formboard_utils.calculate_location(instance)

        svg_px_x = x * 96
        svg_px_y = y * -96

        if item_type == "flagnote":
            if instance.get("note_parent") in ["", None]:
                continue

            flagnote_position_counter[instance.get("parent_instance")] = flagnote_position_counter.get(instance.get("parent_instance"), 0) + 1

            # Unpack positions of note and leader
            x_note, y_note, flagnote_orientation = formboard_utils.calculate_location({
                "instance_name": instance.get("instance_name"),
                "parent_csys_instance_name": instance.get("parent_instance"),
                "parent_csys_outputcsys_name": f"flagnote-{flagnote_position_counter[instance.get("parent_instance")]}",
            })
            x_leader, y_leader, angle_leader = 0,0,0

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


# ==================================================================================================
# write the svg file with group structure backbone
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


# ==================================================================================================
# copy in instance content
for instance in input_instances:
    item_type = instance.get("item_type", "").strip()
    if instance.get("instance_name") in printable_instances:

        # === handle flagnotes ===
        if instance.get("item_type") == "flagnote":
            flagnote_location = os.path.join(
                dirpath(None),
                "instance_data",
                "flagnote",
                instance.get("instance_name"),
            )
            make_new_flagnote_drawing(instance, flagnote_location)
            svg_utils.find_and_replace_svg_group(
                os.path.join(
                    flagnote_location, f"{instance.get("instance_name")}-drawing.svg"
                ),
                instance.get("instance_name"),
                path("output svg"),
                instance.get("instance_name"),
            )

        # === handle segments ===
        elif instance.get("item_type") in ["segment", "flagnote"]:
            # make as needed, edit this section to reference other segment drawings
            generated_instance_location = os.path.join(
                dirpath(None),
                "instance_data",
                "macro",
                f"{artifact_id}-{instance.get("instance_name")}",
            )
            if instance.get("item_type") == "segment":
                make_new_segment_drawing(instance, generated_instance_location)
            svg_utils.find_and_replace_svg_group(
                os.path.join(
                    generated_instance_location,
                    f"{artifact_id}-{instance.get("instance_name")}-drawing.svg",
                ),
                instance.get("instance_name"),
                path("output svg"),
                instance.get("instance_name"),
            )

        else:  # pull from project-level instance_data
            svg_utils.find_and_replace_svg_group(
                os.path.join(
                    fileio.dirpath(None),  # project root
                    "instance_data",
                    instance.get("item_type"),
                    instance.get("instance_name"),
                    f"{instance.get("instance_name")}-drawing.svg",
                ),
                instance.get("instance_name"),
                path("output svg"),
                instance.get("instance_name"),
            )
