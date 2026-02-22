from harnice import fileio
import os

artifact_mpn = "basic_segment_generator"

"""
args:

- instance: dict from instances list. one instance allowed. requires length, diameter, optionally uses length_tolerance
- dimension: int, 0 to 100. 0 the dimension is fully transparent (invisible), 100 is fully opaque
- dimension_units: mm, in, or ft
- scale: scale of the formboard, used to correct dimension size
"""


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


# =============== CALCULATIONS ===============
# Optional args (dimension opacity 0–100, dimension_units, scale for dimension size)
_g = globals()
_dimension = _g.get("dimension", 50)
_dimension = int(_dimension) if _dimension is not None else 50
_dimension_units = (_g.get("dimension_units") or "in").strip().lower()
_scale = float(_g.get("scale", 1.0)) if _g.get("scale") is not None else 1.0

length_inches = float(instance.get("length", 0))
svg_length = length_inches * 96
svg_diameter = float(instance.get("diameter", 1)) * 96

outline_thickness = 0.05 * 96
centerline_thickness = 0.015 * 96
half_svg_diameter = svg_diameter / 2

# Dimension: 1 inch offset below segment; base sizes (svg_utils.table defaults), then scaled
dim_offset = (half_svg_diameter / _scale) + 24  # px
arrow_size = 4  # px
dim_stroke_width = 1  # px
text_pad = 3  # px
text_font_size = 8  # px
text_font_family = "helvetica"

# Dimension units: convert length for label (instance length is in inches)
if _dimension_units == "mm":
    dim_value = length_inches * 25.4
    unit_str = " mm"
elif _dimension_units == "ft":
    dim_value = length_inches / 12.0
    unit_str = " ft"
else:
    dim_value = length_inches
    unit_str = " in"

dim_label_text = (
    f"{dim_value} {instance.get('length_tolerance', '')}".strip() + unit_str
)
# Approximate text box width (units per character for font-size 12)
label_width = max(
    len(dim_label_text) * 6 + 2 * text_pad,
    12,
)
label_height = text_font_size + 2 * text_pad

# Scale dimension-related SVG features by 1/scale
arrow_size_s = arrow_size / _scale
dim_stroke_width_s = dim_stroke_width / _scale
text_pad_s = text_pad / _scale
text_font_size_s = text_font_size / _scale
label_width_s = label_width / _scale
label_height_s = label_height / _scale

# Opacity from dimension (0–100)
dim_opacity = _dimension / 100.0

svg_content = f"""
<svg xmlns="http://www.w3.org/2000/svg" width="{svg_length}" height="{svg_diameter + 2}" viewBox="0 {-half_svg_diameter} {svg_length} {svg_diameter + 2}">
    <g id="{instance.get("instance_name")}-contents-start">
        <line x1="0" y1="0" x2="{svg_length}" y2="0" stroke="black" stroke-width="{svg_diameter}" />
        <line x1="0" y1="0" x2="{svg_length}" y2="0" stroke="white" stroke-width="{svg_diameter - outline_thickness}" />
        <line x1="0" y1="0" x2="{svg_length}" y2="0" stroke="black" style="stroke-width:{centerline_thickness};stroke-dasharray:18,18;stroke-dashoffset:0" />
        <!-- Dimension (opacity from dimension 0–100, sizes scaled by 1/scale) -->
        <g opacity="{dim_opacity}">
            <line x1="0" y1="0" x2="0" y2="{dim_offset}" stroke="black" stroke-width="{dim_stroke_width_s}" />
            <line x1="{svg_length}" y1="0" x2="{svg_length}" y2="{dim_offset}" stroke="black" stroke-width="{dim_stroke_width_s}" />
            <line x1="{arrow_size_s}" y1="{dim_offset}" x2="{svg_length - arrow_size_s}" y2="{dim_offset}" stroke="black" stroke-width="{dim_stroke_width_s}" />
            <path d="M 0,{dim_offset} L {arrow_size_s},{dim_offset - arrow_size_s / 2} L {arrow_size_s},{dim_offset + arrow_size_s / 2} z" fill="black" />
            <path d="M {svg_length},{dim_offset} L {svg_length - arrow_size_s},{dim_offset - arrow_size_s / 2} L {svg_length - arrow_size_s},{dim_offset + arrow_size_s / 2} z" fill="black" />
            <rect x="{svg_length / 2 - label_width_s / 2}" y="{dim_offset - label_height_s / 2}" width="{label_width_s}" height="{label_height_s}" fill="white" />
            <text x="{svg_length / 2}" y="{dim_offset}" font-size="{text_font_size_s}px" font-family="{text_font_family}" text-anchor="middle" dominant-baseline="middle" fill="black" id="dim-label-text">{dim_label_text}</text>
        </g>
    </g>
    <g id="{instance.get("instance_name")}-contents-end"></g>
</svg>
"""

with open(path("drawing"), "w") as svg_file:
    svg_file.write(svg_content)
