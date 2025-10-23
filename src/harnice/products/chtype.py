import os
import ast
from harnice import library_utils, fileio


def path(channel_type):
    """
    Args:
        channel_type: tuple like (chid, lib_repo) or string like "(5, '...')"
    """
    chid, lib_repo = parse(channel_type)
    base_dir = library_utils.get_local_path(lib_repo)
    return os.path.join(base_dir, "channel_types", "channel_types.tsv")


def parse(val):
    """Convert stored string into a tuple (chid:int, lib_repo:str)."""
    if not val:
        return None
    if isinstance(val, tuple):
        chid, lib_repo = val
    else:
        chid, lib_repo = ast.literal_eval(str(val))
    return (int(chid), str(lib_repo).strip())


def compatibles(channel_type):
    """
    Look up compatible channel_types for the given channel_type.
    Splits the TSV field by commas and parses each entry into (chid, lib_repo).
    """
    channel_type_id, lib_repo = parse(channel_type)
    for row in fileio.read_tsv(path((channel_type_id, lib_repo))):
        if str(channel_type_id) != str(row.get("channel_type_id")):
            continue

        signals_str = row.get("compatible_channel_types", "").strip()
        if not signals_str:
            return []

        values = [v.strip() for v in signals_str.split(";") if v.strip()]
        parsed = []
        for v in values:
            parsed.append(parse(v))
        return parsed

    return []


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
