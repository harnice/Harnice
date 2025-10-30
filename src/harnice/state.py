import re

#not initializing these variables so that a NameError is raised if they are not set
def set_pn(x):
    global pn
    pn = x

def set_rev(x):
    global rev
    rev = x

def set_net(x):
    global net
    net = x

def set_file_structure(x):
    global file_structure
    file_structure = x

def partnumber(format):
    # Returns part numbers in various formats based on the current working directory

    # given a part number "pppppp-revR"

    # format options:
    # "pn-rev"    returns "pppppp-revR"
    # "pn"        returns "pppppp"
    # "rev"       returns "revR"
    # "R"         returns "R"

    pn_rev = f"{pn}-rev{rev}"

    if format == "pn-rev":
        return pn_rev

    elif format == "pn":
        match = re.search(r"-rev", pn_rev)
        if match:
            return pn_rev[: match.start()]

    elif format == "rev":
        match = re.search(r"-rev", pn_rev)
        if match:
            return pn_rev[match.start() + 1 :]

    elif format == "R":
        match = re.search(r"-rev", pn_rev)
        if match:
            return pn_rev[match.start() + 4 :]

    else:
        raise ValueError("Function 'partnumber' not presented with a valid format")