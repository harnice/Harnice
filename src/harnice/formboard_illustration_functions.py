import os
import math
import instances_list
import svg_utils
import fileio
from collections import defaultdict
import component_library

def make_new_formboard_master_svg():
    filepath = fileio.path("formboard master svg")
    if os.path.exists(filepath):
        os.remove(filepath)

    instances = instances_list.read_instance_rows()
    excluded_item_types = {"Cable", "Node"}

    # Group instances by item_type
    grouped_instances = defaultdict(list)
    for instance in instances:
        item_type = instance.get("item_type", "").strip()
        if item_type and item_type not in excluded_item_types:
            grouped_instances[item_type].append(instance)

    # Prepare lines for SVG content
    content_lines = []
    for item_type, items in grouped_instances.items():
        content_lines.append(f'    <g id="{item_type}">')
        for instance in items:
            instance_name = instance.get("instance_name", "")
            if not instance_name:
                continue

            x, y, angle = calculate_formboard_location(instance_name)

            try:
                inner_svg = component_library.copy_svg_data(instance_name)
            except Exception as e:
                raise RuntimeError(f"Failed to read SVG data for {instance_name}: {e}")

            px_x = x * 96
            px_y = y * 96

            if instance.get("absolute_rotation") != "":
                angle = float(instance.get("absolute_rotation"))

            #transform harnice csys (right-hand rule, ccw is positive angle, up is +), to svg csys (cw is positive angle, up is -)
            svg_px_x = px_x
            svg_px_y = -1 * px_y
            svg_angle = -1 * angle

            content_lines.append(f'      <g transform="translate({svg_px_x},{svg_px_y}) rotate({svg_angle})">'
            )
            content_lines.append(inner_svg)
            content_lines.append('      </g>')
        content_lines.append('    </g>')

    # Write full SVG
    with open(filepath, 'w') as f:
        f.write('<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n')
        f.write('<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="1000" height="1000">\n')
        f.write('  <g id="formboard-master-contents-start">\n')
        f.writelines(line + '\n' for line in content_lines)
        f.write('  </g>\n')
        f.write('  <g id="formboard-master-contents-end">\n')
        f.write('  </g>\n')
        f.write('</svg>\n')


def calculate_formboard_location(instance_name):
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

    x_pos = 0.0
    y_pos = 0.0
    angle = 0.0  # degrees

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

        #print(f"After {name}: {x_pos}, {y_pos}, {angle}")
    return x_pos, y_pos, angle

def update_segment_instances():
    instances = instances_list.read_instance_rows()

    for instance in instances:
        if instance.get("item_type") == "Segment":
            segment_name = instance.get("instance_name", "").strip()
            if not segment_name:
                continue

            try:
                # Get length and diameter in inches and convert to pixels
                length_in = float(instance.get("length", 0))
                diameter_in = float(instance.get("diameter", 1))
                length = 96 * length_in
                diameter = 96 * diameter_in

                outline_thickness = 0.05 * 96
                centerline_thickness = 0.015 * 96

                half_diameter = diameter / 2

                svg_content = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{length}" height="{diameter}" viewBox="0 {-half_diameter} {length} {diameter}">
                    <line x1="0" y1="0" x2="{length}" y2="0" stroke="black" stroke-width="{diameter}" />
                    <line x1="0" y1="0" x2="{length}" y2="0" stroke="white" stroke-width="{diameter - outline_thickness}" />
                    <line x1="0" y1="0" x2="{length}" y2="0" stroke="black" style="stroke-width:{centerline_thickness};stroke-dasharray:18,18;stroke-dashoffset:0" />
                </svg>'''
                segment_dir = os.path.join(fileio.dirpath("editable_component_data"), segment_name)
                os.makedirs(segment_dir, exist_ok=True)

                output_filename = os.path.join(segment_dir, f"{segment_name}-drawing.svg")

                with open(output_filename, 'w') as svg_file:
                    svg_file.write(svg_content)

                component_library.add_filename_to_drawing_instance_list(os.path.basename(segment_dir))

                print(f"Built segment SVG for segment {segment_name} (deleted existing if present)")

            except Exception as e:
                print(f"Error processing segment {segment_name}: {e}")