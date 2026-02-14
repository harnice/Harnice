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
Resolve the on-disk path to the `channel_types.tsv` file for a given
channel type.

**Args**

- `channel_type`: Channel type identifier in standard tuple format
    `(channel_type_id, lib_repo)` or any string representation that `parse`
    can understand (for example `"(5, 'https://github.com/harnice/harnice')"`).

**Returns**

- `str`: Absolute path to the `channel_types/channel_types.tsv` file inside
    the library repository that owns the given channel type.

**Notes**

- This does **not** filter rows; it only locates the TSV file that defines
    all channel types for the given `lib_repo`.
    """
    chid, lib_repo = parse(channel_type)
    base_dir = library_utils.get_local_path(lib_repo)
    return os.path.join(base_dir, "channel_types", "channel_types.tsv")


def parse(val):
    """
Convert stored string into a tuple (chid:int, lib_repo:str).
Handles both single tuples and extracts first tuple from lists.
    """
    if val in [None, ""]:
        raise ValueError("channel type is blank")
    if isinstance(val, tuple):
        chid, lib_repo = val
    else:
        parsed = ast.literal_eval(str(val))
        # If it's a list, take the first tuple
        if not isinstance(parsed, tuple):
            if isinstance(parsed, list):
                chid, lib_repo = parsed[0]
            else:
                raise ValueError(f"channel type {val} that is being parsed is malformed. Channel types must be touples or list of touples in format (int, string)")
        else:
            chid, lib_repo = parsed
    return (int(chid), str(lib_repo).strip())


def compatibles(channel_type):
    """
Look up other channel types that are declared as compatible with the given
channel type.

**Args**

- `channel_type`: Channel type identifier in standard tuple format
    `(channel_type_id, lib_repo)` or any string representation that `parse`
    can understand.

**Returns**

- `list[tuple[int, str]]`: List of `(channel_type_id, lib_repo)` tuples taken
    directly from the `compatible_channel_types` column of `channel_types.tsv`.
    Returns an empty list if no compatibles are defined or if the channel type
    cannot be found.

**Data format**

- The `compatible_channel_types` column must be an AST-parseable Python value:
    - Single tuple: `(1, "library_repo")`
    - List of tuples: `[(1, "library_repo"), (2, "library_repo")]`
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
    """
Return the given channel type plus all channel types declared as compatible
with it.

**Args**

- `channel_type`: Channel type identifier in standard tuple format
    `(channel_type_id, lib_repo)` or any string representation that `parse`
    can understand.

**Returns**

- `list[tuple[int, str]]`: List of `(channel_type_id, lib_repo)` tuples where
    the first entry is the parsed `channel_type` itself and the remaining
    entries are the compatibles returned by `compatibles(channel_type)`.

**Typical use**

- Use this when validating or mapping channels and you want to treat a
    channel type as valid if it is either exactly the requested type or
    explicitly listed as compatible with it.
    """
    output = []
    output.append(parse(channel_type))
    for compatible in compatibles(channel_type):
        output.append(compatible)
    return output


def signals(channel_type):
    """
Return the list of signal names associated with a specific channel type.

**Args**

- `channel_type`: Channel type identifier in standard tuple format
    `(channel_type_id, lib_repo)` or any string representation that `parse`
    can understand.

**Returns**

- `list[str]`: List of signal names from the `signals` column of
    `channel_types.tsv` for the matching `channel_type_id`. If the column is
    blank or the channel type cannot be found, returns an empty list.

**Data format**

- The `signals` column is expected to be a comma-separated string, for
    example: `"CAN_H, CAN_L, SHIELD"`.
    """
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


def attribute(channel_type, attribute):
    """
Read any additional column from `channel_types.tsv` for a given channel
type.

**Args**

- `channel_type`: Channel type identifier in standard tuple format
    `(channel_type_id, lib_repo)` or any string representation that `parse`
    can understand.
- `attribute`: Column header name in `channel_types.tsv` for the value you
    want to read (for example `"description"`, `"notes"`, `"voltage_rating"`).

**Returns**

- `Any`: Value stored in the requested `attribute` column for the matching
    `channel_type_id`. Returns an empty list `[]` if the channel type cannot
    be found.

**Notes**

- Use this for any per-channel-type metadata you've added as extra columns
    beyond the core ones like `channel_type_id`, `signals`, and
    `compatible_channel_types`.
    """
    chid, lib_repo = parse(channel_type)

    ch_types_tsv_path = os.path.join(
        library_utils.get_local_path(lib_repo), "channel_types", "channel_types.tsv"
    )

    for row in fileio.read_tsv(ch_types_tsv_path):
        if str(row.get("channel_type_id", "")).strip() == str(chid):
            return row.get(attribute)
    return []
