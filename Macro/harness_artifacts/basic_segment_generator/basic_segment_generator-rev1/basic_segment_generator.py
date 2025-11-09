import os
from harnice import fileio

artifact_mpn = "basic_segment_generator"

# =============== PATHS ===============
def file_structure():
    return {
        "instance_data": {
            "imported_instances": {
                "macro": {
                    artifact_id: {
                        f"{state.partnumber('pn-rev')}-{artifact_id}-drawing-master.svg": "master svg",
                        f"{artifact_id}-imported-instances": {},
                    }
                }
            }
        }
    }


try:
    instance.get("instance_name")
except:
    raise ValueError("please pass an instance dict as argument 'instance' to this macro")

if instance.get("item_type") != "segment":
    raise ValueError(f"basic_segment_generator can only be used to generate segments, not {instance.get('item_type')}")

os.makedirs(fileio.dirpath(f"{artifact_id}-imported-instances", structure_dict=file_structure()), exist_ok=True)

length = 96 * float(instance.get("length", 0))
diameter = 96 * float(instance.get("diameter", 1))

outline_thickness = 0.05 * 96
centerline_thickness = 0.015 * 96
half_diameter = diameter / 2

svg_content = f"""
<svg xmlns="http://www.w3.org/2000/svg" width="{length}" height="{diameter}" viewBox="0 {-half_diameter} {length} {diameter}">
    <g id="{instance.get("instance_name")}-contents-start">
        <line x1="0" y1="0" x2="{length}" y2="0" stroke="black" stroke-width="{diameter}" />
        <line x1="0" y1="0" x2="{length}" y2="0" stroke="white" stroke-width="{diameter - outline_thickness}" />
        <line x1="0" y1="0" x2="{length}" y2="0" stroke="black" style="stroke-width:{centerline_thickness};stroke-dasharray:18,18;stroke-dashoffset:0" />
    </g>
    <g id="{instance.get("instance_name")}-contents-end"></g>
</svg>
"""

with open(fileio.path("master svg", structure_dict=file_structure()), "w") as svg_file:
    svg_file.write(svg_content)