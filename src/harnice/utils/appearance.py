import ast
import webcolors

"""
Appearance guide:
    color lookup: https://www.w3.org/TR/SVG11/types.html#ColorKeywords
    add the following dictionary-formatted string to a field in the instances list


format: design your macros to be able to parse this, define your cables to conform to this
    {"base_color":"","parallelstripe":["",""],"perpstripe":[], "twisted":None}

    
"""


def parse(val):
    """
    Parse appearance dictionary, converting color names and shorthand hex to full hex.
    No validation or safeguards.
    """
    if not val:
        return None

    data = val if isinstance(val, dict) else ast.literal_eval(str(val))
    result = {}

    for key, value in data.items():
        # lists → normalize each element
        if isinstance(value, list):
            parsed = []
            for c in value:
                c = c.strip().lower()
                if c.startswith("#") and len(c) == 4:
                    c = "#" + "".join(ch * 2 for ch in c[1:])
                if not c.startswith("#"):
                    c = webcolors.name_to_hex(c)
                parsed.append(c)
            result[key] = parsed
        # single string → normalize directly
        elif isinstance(value, str):
            c = value.strip().lower()
            if c.startswith("#") and len(c) == 4:
                c = "#" + "".join(ch * 2 for ch in c[1:])
            if not c.startswith("#"):
                c = webcolors.name_to_hex(c)
            result[key] = c
        else:
            result[key] = value

    return result
