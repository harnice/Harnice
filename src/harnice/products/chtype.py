import os
import ast
from harnice import fileio
from harnice.utils import library_utils


def file_structure():
    return {}


def generate_structure():
    pass


def path(channel_type):
    """
    Args:
        channel_type: tuple like (chid, lib_repo) or string like "(5, '...')"
    """
    chid, lib_repo = parse(channel_type)
    base_dir = library_utils.get_local_path(lib_repo)
    return os.path.join(base_dir, "channel_types", "channel_types.tsv")


def parse(val):
    """
    Convert stored string into a tuple (chid:int, lib_repo:str).
    Handles both single tuples and extracts first tuple from lists.
    """
    if not val:
        return None
    if isinstance(val, tuple):
        chid, lib_repo = val
    else:
        parsed = ast.literal_eval(str(val))
        # If it's a list, take the first tuple
        if isinstance(parsed, list):
            chid, lib_repo = parsed[0]
        else:
            chid, lib_repo = parsed
    return (int(chid), str(lib_repo).strip())

def compatibles(channel_type):
    """
    Look up compatible channel_types for the given channel_type.
    Expects compatible_channel_types column to contain AST-parseable format:
    - Single tuple: (1, 'library_repo')
    - List of tuples: [(1, 'library_repo'), (2, 'library_repo')]
    """
    channel_type_id, lib_repo = parse(channel_type)
    
    for row in fileio.read_tsv(path((channel_type_id, lib_repo))):
        if int(row.get("channel_type_id")) == channel_type_id:
            signals_str = row.get("compatible_channel_types", "").strip()
            if not signals_str:
                return []
            
            # Parse the AST-formatted string
            parsed_value = ast.literal_eval(signals_str)
            
            # Normalize to list format
            if isinstance(parsed_value, tuple):
                # Single tuple, wrap it in a list
                return [parsed_value]
            elif isinstance(parsed_value, list):
                # Already a list of tuples
                return parsed_value
            else:
                return []
    
    return []


def is_or_is_compatible_with(channel_type):
    output = []
    output.append(parse(channel_type))
    for compatible in compatibles(channel_type):
        output.append(compatible)
    return output


# search channel_types.tsv
def signals(channel_type):
    chid, lib_repo = parse(channel_type)

    ch_types_tsv_path = os.path.join(
        library_utils.get_local_path(lib_repo), "channel_types", "channel_types.tsv"
    )

    for row in fileio.read_tsv(ch_types_tsv_path):
        if str(row.get("channel_type_id", "")).strip() == str(chid):
            return [
                sig.strip() for sig in row.get("signals", "").split(",") if sig.strip()
            ]
    return []

# search channel_types.tsv
def attribute(channel_type, attribute):
    """If you've defined other columns in your channel type, this will return that

**Args**

 - `channel_type` standard touple-format
 - `attribute` header name of the attribute you need to find
    """
    chid, lib_repo = parse(channel_type)

    ch_types_tsv_path = os.path.join(
        library_utils.get_local_path(lib_repo), "channel_types", "channel_types.tsv"
    )

    for row in fileio.read_tsv(ch_types_tsv_path):
        if str(row.get("channel_type_id", "")).strip() == str(chid):
            return row.get(attribute)
    return []
