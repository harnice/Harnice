import os
import json
import math
from collections import defaultdict
from harnice import svg_outputs, flagnotes, rev_history, svg_utils, instances_list, fileio

artifact_mpn = "standard_harnice_formboard"

#=============== PATHS ===============
def path(target_value):
    base_path = os.path.join(fileio.dirpath("artifacts"), artifact_mpn, artifact_id)
    if target_value == "output svg":
        return os.path.join(base_path, f"{fileio.partnumber("pn-rev")}-{artifact_id}-master.svg")
    if target_value == "show hide":
        return os.path.join(base_path, f"{fileio.partnumber("pn-rev")}-{artifact_id}-showhide.json")
    else:
        raise KeyError(f"Filename {target_value} not found in {artifact_mpn} file tree")

def update_showhide():
    # === Titleblock Defaults ===
    blank_setup = {
        "hide_instances":{},
        "hide_item_types":{}
    }

    return blank_setup

def calculate_formboard_location(instance_name, origin):
    """
    Given an instance_name, recursively trace up the parent_csys chain 
    until reaching an instance with no parent_csys defined.

    After tracing, iterate back down the chain, performing the translate/rotate algorithm,
    but excluding the last instance (the input instance itself) from movement calculations.

    Returns:
        (component_x_pos, component_y_pos, component_angle)
    """
    instances = instances_list.read_instance_rows()
    instances_lookup = {row['instance_name']: row for row in instances}

    chain = []
    current = instance_name

    while current:
        chain.append(current)
        row = instances_lookup.get(current)
        if not row:
            break
        parent = row.get('parent_csys', '').strip()
        if not parent:
            break
        current = parent

    x_pos = origin[0]
    y_pos = origin[1]
    angle = origin[2]  # degrees

    # Skip the last element (the starting instance)
    for name in reversed(chain[1:]):
        row = instances_lookup.get(name, {})

        translate_x = row.get('translate_x', '').strip()
        translate_y = row.get('translate_y', '').strip()
        rotate_csys = row.get('rotate_csys', '').strip()

        try:
            translate_x = float(translate_x) if translate_x else 0.0
        except ValueError:
            translate_x = 0.0

        try:
            translate_y = float(translate_y) if translate_y else 0.0
        except ValueError:
            translate_y = 0.0

        try:
            rotate_csys = float(rotate_csys) if rotate_csys else 0.0
        except ValueError:
            rotate_csys = 0.0

        rad = math.radians(angle)

        x_pos += math.cos(rad) * translate_x - math.sin(rad) * translate_y
        y_pos += math.sin(rad) * translate_x + math.cos(rad) * translate_y
        angle += rotate_csys

    return x_pos, y_pos, angle

#=================================================
#FIRST, UPDATE SEGMENT INSTANCES
instances = instances_list.read_instance_rows()

for instance in instances:
    if instance.get("item_type") == "Segment":
        segment_name = instance.get("instance_name", "").strip()
        if not segment_name:
            continue

        try:
            length_in = float(instance.get("length", 0))
            diameter_in = float(instance.get("diameter", 1))
            length = 96 * length_in
            diameter = 96 * diameter_in

            outline_thickness = 0.05 * 96
            centerline_thickness = 0.015 * 96
            half_diameter = diameter / 2

            svg_content = f'''
            <svg xmlns="http://www.w3.org/2000/svg" width="{length}" height="{diameter}" viewBox="0 {-half_diameter} {length} {diameter}">
                <g id="{instance.get("instance_name")}-contents-start">
                    <line x1="0" y1="0" x2="{length}" y2="0" stroke="black" stroke-width="{diameter}" />
                    <line x1="0" y1="0" x2="{length}" y2="0" stroke="white" stroke-width="{diameter - outline_thickness}" />
                    <line x1="0" y1="0" x2="{length}" y2="0" stroke="black" style="stroke-width:{centerline_thickness};stroke-dasharray:18,18;stroke-dashoffset:0" />
                </g>
                <g id="{instance.get("instance_name")}-contents-end"></g>
            </svg>
            '''
            segment_dir = os.path.join(fileio.dirpath("uneditable_instance_data"), segment_name)
            os.makedirs(segment_dir, exist_ok=True)

            output_filename = os.path.join(segment_dir, f"{segment_name}-drawing.svg")
            with open(output_filename, 'w') as svg_file:
                svg_file.write(svg_content)

        except Exception as e:
            print(f"Error processing segment {segment_name}: {e}")

#==========================
instances = instances_list.read_instance_rows()
printable_item_types = {"Connector", "Backshell", "Segment", "Flagnote", "Flagnote leader"}

rotation = 0 #TODO: FIGURE OUT HOW TO PASS THIS IN SOMEWHERE
if rotation == "":
    raise KeyError(f"[ERROR] Rotation '{rotation}' not found in harnice output contents")
origin = [0, 0, rotation]

#TODO: figure out scales
#scale_name = page_setup_contents["formboards"].get(formboard_name, {}).get("scale", "A")
scale = 1 # page_setup_contents["scales"].get(scale_name)

# Group instances by item_type
grouped_instances = defaultdict(list)
for instance in instances:
    item_type = instance.get("item_type", "").strip()
    if item_type and item_type in printable_item_types:
        grouped_instances[item_type].append(instance)

# Prepare lines for SVG content
content_lines = []
#TODO: fix hide stuff
#formboard = page_setup_contents["formboards"].get(formboard_name, {})
hide_filters = {} #formboard.get("hide_instances", {})

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

        if instance.get("absolute_rotation") != "":
            angle = float(instance.get("absolute_rotation"))

        if instance.get("item_type") == "Segment":
            angle += origin[2]

        svg_px_x = px_x
        svg_px_y = -1 * px_y
        svg_angle = -1 * angle

        if not item_type == "Flagnote":
            content_lines.append(f'      <g id="{instance_name}-contents-start" inkscape:label="{instance_name}-contents-start" transform="translate({svg_px_x},{svg_px_y}) rotate({svg_angle})">')
            content_lines.append('      </g>')
            content_lines.append(f'      <g id="{instance_name}-contents-end" inkscape:label="{instance_name}-contents-end"></g>')
        else:
            content_lines.append(f'      <g id="{instance_name}-translate" transform="translate({svg_px_x},{svg_px_y}) rotate({svg_angle})">')
            content_lines.append(f'        <g id="{instance_name}-scale" transform="scale({1 / scale})">')
            content_lines.append(f'          <g id="{instance_name}-contents-start" inkscape:label="{instance_name}-contents-start">')
            content_lines.append(f'          </g>')
            content_lines.append(f'          <g id="{instance_name}-contents-end" inkscape:label="{instance_name}-contents-end"></g>')
            content_lines.append(f'        </g>')
            content_lines.append(f'      </g>')

    content_lines.append('    </g>')

# Write full SVG
with open(path("output svg"), 'w') as f:
    f.write('<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n')
    f.write('<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="1000" height="1000">\n')
    f.write(f'  <g id="{artifact_mpn}-contents-start">\n')
    f.write(f'    <g id="{artifact_mpn}-scale_group" transform="scale({scale})">\n')
    f.writelines(line + '\n' for line in content_lines)
    f.write('    </g>\n')
    f.write('  </g>\n')
    f.write(f'  <g id="{artifact_mpn}-contents-end">\n')
    f.write('  </g>\n')
    f.write('</svg>\n')

#now that the SVG has been written, copy the connector content in:
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

        if item_type in {"Connector", "Backshell"}:
            instance_data_dir = fileio.dirpath("editable_instance_data")
        elif item_type == "Flagnote leader":
            instance_data_dir = os.path.join(fileio.dirpath("uneditable_instance_data"), formboard_name)
        else:
            instance_data_dir = fileio.dirpath("uneditable_instance_data")

        #TODO: fix flagnotes first before uncommenting
        """
        svg_utils.find_and_replace_svg_group(
            path("output svg"),
            os.path.join(
                instance_data_dir, 
                instance.get("instance_name"),
                f"{instance.get("instance_name")}-drawing.svg"
            ),
            instance.get("instance_name"),
            instance.get("instance_name")
        )
        """
