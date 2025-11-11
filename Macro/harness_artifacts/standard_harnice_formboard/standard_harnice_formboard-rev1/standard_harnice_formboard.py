import math
import re
import os
from collections import defaultdict
from harnice import fileio, state
from harnice.products import harness
from harnice.utils import library_utils, formboard_utils, svg_utils, feature_tree_utils

artifact_mpn = "standard_harnice_formboard"

"""
Args:
artifact_id : "unique identifier for this instance of the macro (drawing-1)"
scale : scale factor for the drawing
rotation : rotation of the drawing in degrees=
"""


# =============== PATHS ===================================================================================
def macro_file_structure(instance_name=None, item_type=None):
    return {
        f"{state.partnumber('pn-rev')}-{artifact_id}-master.svg": "output svg",
    }

if base_directory is None:  #path between cwd and the file structure for this macro
    base_directory = os.path.join("instance_data", "macro", artifact_id)

def path(target_value):
    return fileio.path(target_value, structure_dict=macro_file_structure(), base_directory=base_directory)

def dirpath(target_value):
    # target_value = None will return the root of this macro
    return fileio.dirpath(target_value, structure_dict=macro_file_structure(), base_directory=base_directory)
# ==========================================================================================================

instances = fileio.read_tsv("instances list") # only need to call this once
printable_item_types = {"connector", "backshell", "segment", "flagnote"} # add content here as needed

# define coordinate system
try:
    if not rotation:
        rotation = 0
except NameError:
    rotation = 0
origin = [0, 0, rotation]


# ====================================================
#        MAKE FLAGNOTE DRAWINGS
# ====================================================
instances = fileio.read_tsv("instances list")

for instance in instances:
    if instance.get("item_type") != "flagnote":
        continue

    if instance.get("mpn") in ["", None]:
        continue

    # === Pull drawings into this macro and define filepath ===
    # edit this section if you want to reference different flagnote drawings)
    flagnote_import_path = os.path.join(
        dirpath(None),
        "instance_data",
        "flagnote",
        instance.get("instance_name")
    )
    library_utils.pull(
        instance, 
        destination_directory=flagnote_import_path
    )
    flagnote_drawing_path = os.path.join(
        flagnote_import_path,
        f"{instance.get("instance_name")}-drawing.svg"
    )

    # === Perform text replacement on known drawing path ===
    with open(flagnote_drawing_path, "r", encoding="utf-8") as f:
        svg = f.read()

    svg = re.sub(r">flagnote-text<", f">{instance.get('bubble_text')}<", svg)

    with open(flagnote_drawing_path, "w", encoding="utf-8") as f:
        f.write(svg)

# ====================================================
#        MAKE SEGMENT DRAWINGS
# ====================================================
for instance in instances:
    if instance.get("item_type") != "segment":
        continue

    segment_base_dir = os.path.join(dirpath(None), "instance_data", "macro", instance.get("instance_name"))
    feature_tree_utils.run_macro(
        "basic_segment_generator",
        "harness_artifacts", 
        "https://github.com/harnice/harnice-library-public", 
        artifact_id=instance.get("instance_name"), 
        instance=instance,
        base_directory=segment_base_dir
    )


# ==========================
#        CONSTRUCT SVG ELEMENTS
# ==========================
# Group instances by item_type
grouped_instances = defaultdict(list)
for instance in instances:
    item_type = instance.get("item_type", "").strip()
    if item_type in printable_item_types:
        grouped_instances[item_type].append(instance)

# Prepare lines for SVG content
content_lines = []

printable_instances = set()

for item_type, items in grouped_instances.items():
    content_lines.append(f'    <g id="{item_type}" inkscape:label="{item_type}">')
    for instance in items:
        # =================================
        if instance.get("item_type") not in printable_item_types:
            continue

        # call continue more times here (after some logic) if you don't want to print this instance, for example:

        # if instance.get("item_type") == "flagnote" and instance.get("note_type") != "part_name":
        #     continue
        # =================================
        printable_instances.add(instance.get("instance_name"))

        instance_name = instance.get("instance_name")

        x, y, angle = formboard_utils.calculate_location(instance_name, origin)

        px_x = x * 96
        px_y = y * 96

        if instance.get("item_type") == "segment":
            angle += origin[2]

        if instance.get("absolute_rotation") != "":
            angle = float(instance.get("absolute_rotation"))

        if instance.get("item_type") == "segment":
            angle += origin[2]

        svg_px_x = px_x
        svg_px_y = -1 * px_y
        svg_angle = -1 * angle

        if item_type == "flagnote":
            if instance.get("parent_instance") in ["", None]:
                continue

            # Unpack both positions
            x_note, y_note, flagnote_orientation = formboard_utils.calculate_location(
                instance_name, origin
            )
            x_leader, y_leader, angle_leader = formboard_utils.calculate_location(
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
with open(fileio.path("output svg", structure_dict=macro_file_structure(), base_directory=base_directory), "w") as f:
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
    if instance.get("instance_name") in printable_instances:

        # skip flagnotes that have no mpn (aka buildnotes with no affected_instance, etc)
        if instance.get("item_type") == "flagnote" and instance.get("mpn") in [None, ""]:
            continue

        if instance.get("item_type") in ["segment", "flagnote"]: #pull these item types from this macro's instance_data
            svg_utils.find_and_replace_svg_group(
                fileio.path("output svg", structure_dict=macro_file_structure(), base_directory=base_directory),
                fileio.path("instance drawing svg", structure_dict=macro_file_structure(instance_name=instance.get("instance_name"), item_type=instance.get("item_type")), base_directory=base_directory),
                instance.get("instance_name"),
                instance.get("instance_name"),
            )
        else: #pull from project-level instance_data
            svg_utils.find_and_replace_svg_group(
                fileio.path("output svg", structure_dict=macro_file_structure(), base_directory=base_directory),
                fileio.path("instance drawing svg", structure_dict=harness.file_structure(instance_name=instance.get("instance_name"), item_type=instance.get("item_type")), base_directory=base_directory),
                instance.get("instance_name"),
                instance.get("instance_name"),
            )
