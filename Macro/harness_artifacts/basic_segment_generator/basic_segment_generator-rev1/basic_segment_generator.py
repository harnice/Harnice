from harnice import fileio, state
import os

artifact_mpn = "basic_segment_generator"

# =============== PATHS ===============
if base_directory == None: #path between cwd and the file structure for this macro
    base_directory = os.path.join("instance_data", "macro", artifact_id)

def macro_file_structure():
    return {
        f"{state.partnumber('pn-rev')}-{artifact_id}-drawing-master.svg": "master svg",
    }

# =============== INPUT CHECKS ===============
try
    instance.get("instance_name")
except:
    raise ValueError("please pass an instance dict as argument 'instance' to this macro")

if instance.get("item_type") != "segment":
    raise ValueError(f"basic_segment_generator can only be used to generate segments, not {instance.get('item_type')}")

# =============== CALCULATIONS ===============
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

with open(fileio.path("master svg", structure_dict=macro_file_structure(), base_directory=base_directory), "w") as svg_file:
    svg_file.write(svg_content)