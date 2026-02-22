from harnice import fileio
import os

artifact_mpn = "basic_segment_generator"


# =============== PATHS ===================================================================================
def macro_file_structure():
    return {
        f"{artifact_id}-drawing.svg": "drawing",
    }


if base_directory == None:  # path between cwd and the file structure for this macro
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


# ==========================================================================================================

# =============== INPUT CHECKS ===============
try:
    instance.get("instance_name")
except:
    raise ValueError(
        "please pass an instance dict as argument 'instance' to this macro"
    )

if instance.get("item_type") != "segment":
    raise ValueError(
        f"basic_segment_generator can only be used to generate segments, not {instance.get('item_type')}"
    )

# Scale: 96 units per inch (match svg_utils.table and drawing units)
dimension_scale = 96

# =============== CALCULATIONS ===============
length = dimension_scale * float(instance.get("length", 0))
diameter = dimension_scale * float(instance.get("diameter", 1))
segment_length_inches = float(instance.get("length", 0))

outline_thickness = 0.05 * dimension_scale
centerline_thickness = 0.015 * dimension_scale
half_diameter = diameter / 2

# Dimension: 1 inch offset below segment; all sizes normalized to scale (svg_utils.table defaults)
dim_offset = 1 * dimension_scale
dim_y = dim_offset
arrow_size = (8 / 96) * dimension_scale
dim_stroke_width = (1 / 96) * dimension_scale
text_pad = (4 / 96) * dimension_scale
# Font from svg_utils.table DEFAULTS
text_font_size = (12 / 96) * dimension_scale
text_font_family = "helvetica"
dim_label_text = (
    f"{instance.get('length')} {instance.get('length_tolerance', '')}".strip() + " in"
)
# Approximate text box width (units per character for font-size 12)
label_width = max(
    len(dim_label_text) * (9 / 96) * dimension_scale + 2 * text_pad,
    (24 / 96) * dimension_scale,
)
label_height = text_font_size + 2 * text_pad

svg_content = f"""
<svg xmlns="http://www.w3.org/2000/svg" width="{length}" height="{diameter}" viewBox="0 {-half_diameter} {length} {diameter}">
    <g id="{instance.get("instance_name")}-contents-start">
        <line x1="0" y1="0" x2="{length}" y2="0" stroke="black" stroke-width="{diameter}" />
        <line x1="0" y1="0" x2="{length}" y2="0" stroke="white" stroke-width="{diameter - outline_thickness}" />
        <line x1="0" y1="0" x2="{length}" y2="0" stroke="black" style="stroke-width:{centerline_thickness};stroke-dasharray:18,18;stroke-dashoffset:0" />
        <!-- Dimension (50% opacity) -->
        <g opacity="0.5">
            <line x1="0" y1="0" x2="0" y2="{dim_y}" stroke="black" stroke-width="{dim_stroke_width}" />
            <line x1="{length}" y1="0" x2="{length}" y2="{dim_y}" stroke="black" stroke-width="{dim_stroke_width}" />
            <line x1="{arrow_size}" y1="{dim_y}" x2="{length - arrow_size}" y2="{dim_y}" stroke="black" stroke-width="{dim_stroke_width}" />
            <path d="M 0,{dim_y} L {arrow_size},{dim_y - arrow_size / 2} L {arrow_size},{dim_y + arrow_size / 2} z" fill="black" />
            <path d="M {length},{dim_y} L {length - arrow_size},{dim_y - arrow_size / 2} L {length - arrow_size},{dim_y + arrow_size / 2} z" fill="black" />
            <rect x="{length / 2 - label_width / 2}" y="{dim_y - label_height / 2}" width="{label_width}" height="{label_height}" fill="white" />
            <text x="{length / 2}" y="{dim_y}" font-size="{text_font_size}px" font-family="{text_font_family}" text-anchor="middle" dominant-baseline="middle" fill="black" id="dim-label-text">{dim_label_text}</text>
        </g>
    </g>
    <g id="{instance.get("instance_name")}-contents-end"></g>
</svg>
"""

with open(path("drawing"), "w") as svg_file:
    svg_file.write(svg_content)
