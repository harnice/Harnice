import ast
import webcolors

"""
Appearance guide:
    color lookup: https://www.w3.org/TR/SVG11/types.html#ColorKeywords
    add the following dictionary-formatted string to a field in the instances list


format: design your macros to be able to parse this, define your cables to conform to this
    {"base_color":"","parallelstripe":["",""],"perpstripe":[], "twisted":None}
    required arg:
        base_color (requires one value)
    optional args:
        parallelstripe (accepts 0-unlimited values in a list)
        perpstripe (accepts 0-unlimited values in a list)
        twisted (accepts 0-one value: None, "RH", "LH)
        outline_color (accepts 0-one value)
    
"""


def parse(val):
    """
    Convert stored string like:
        {base_color:"red", parallelstripe:["#0f0","blue"], perpstripe:[], twisted:"RH"}
    into a dictionary with all colors converted to normalized hex:
        {
            "base_color": "#ff0000",
            "parallelstripe": ["#00ff00", "#0000ff"],
            "perpstripe": [],
            "outline_color": None,
            "twisted": "RH"
        }
    """
    if not val:
        return None

    data = val if isinstance(val, dict) else ast.literal_eval(str(val))
    result = {}

    for key in (
        "base_color",
        "parallelstripe",
        "perpstripe",
        "outline_color",
        "twisted",
    ):
        if key not in data:
            # lists for stripe keys, None for single-value keys
            if key in ("parallelstripe", "perpstripe"):
                result[key] = []
            elif key == "twisted":
                result[key] = None
            else:
                result[key] = None
            continue

        value = data[key]

        # --- handle twisted separately ---
        if key == "twisted":
            if value is None:
                result[key] = None
            elif str(value).upper() in ("RH", "LH"):
                result[key] = str(value).upper()
            else:
                raise ValueError(
                    f"Invalid twisted value: '{value}'. Expected 'RH', 'LH', or None."
                )
            continue

        # --- handle color lists ---
        if isinstance(value, list):
            parsed_colors = []
            for c in value:
                if not c:
                    continue
                c = c.strip().lower()
                if c.startswith("#"):
                    if len(c) == 4:  # short hex
                        c = "#" + "".join(ch * 2 for ch in c[1:])
                    parsed_colors.append(c)
                else:
                    try:
                        parsed_colors.append(webcolors.name_to_hex(c))
                    except ValueError:
                        raise ValueError(f"Unknown color name: '{c}'")
            result[key] = parsed_colors
        else:
            if not value:
                result[key] = None
                continue
            c = value.strip().lower()
            if c.startswith("#"):
                if len(c) == 4:
                    c = "#" + "".join(ch * 2 for ch in c[1:])
                result[key] = c
            else:
                try:
                    result[key] = webcolors.name_to_hex(c)
                except ValueError:
                    raise ValueError(f"Unknown color name: '{c}'")

    return result
