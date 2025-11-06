# ===================== IMPORTS =====================
from harnice import fileio, state
from harnice.lists import instances_list


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

for segment_group in instances_list.list_of_uniques("segment_group"):

    group_items = []
    for instance in instances:
        # Must match segment group
        if instance.get("segment_group") != segment_group:
            continue

        # If item_type is specified, it must match
        if instance.get("item_type") != item_type:
            continue

        group_items.append(instance)

    n = len(group_items)
    if n == 0:
        continue

    # real → svg conversion:
    tx = float(instances_list.attribute_of(segment_group, "translate_x") or 0)
    ty = float(instances_list.attribute_of(segment_group, "translate_y") or 0)
    rot = float(instances_list.attribute_of(segment_group, "absolute_rotation") or 0)
    length = float(instances_list.attribute_of(segment_group, "length") or 0) * 96

    # Flip y and rotation to convert coordinate systems
    ty_svg = -ty
    rot_svg = -rot

    # Center vertically, but invert so positive upward in real becomes downward in SVG
    y_offsets = [-(i - (n - 1) / 2) * segment_spacing for i in range(n)]

    line_elems = []
    for y in y_offsets:
        line_elems.append(
            f'<line x1="0" y1="{y:.3f}" x2="{length:.3f}" y2="{y:.3f}" '
            f'stroke="black" stroke-width="1"/>'
        )

    svg_groups.append(
        f'<g id="{segment_group}" transform="translate({tx:.3f},{ty_svg:.3f}) rotate({rot_svg:.3f})">'
        + "".join(line_elems)
        + "</g>"
    )



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
