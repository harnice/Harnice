import ast

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
    """Convert stored string into a tuple (chid:int, lib_repo:str)."""
    if not val:
        return None
    if isinstance(val, tuple):
        chid, lib_repo = val
    else:
        chid, lib_repo = ast.literal_eval(str(val))
    return (int(chid), str(lib_repo).strip())