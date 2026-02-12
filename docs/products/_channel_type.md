# Channel Types

---

## How are channels mapped?

---

## How to define a new channel type
1. In a repository of your choice (or start with [harnice_library_public](https://github.com/harnice/harnice) on your own branch), navigate to `library_repo/channel_types/channel_types.csv`
1. If you want channel definitions to be private and are therefore working in a private repository, ensure the repo's path is listed in file `library_locations.csv` (located at root of your harnice source code repo). The first column is the URL or traceable path, and the second column is your local path.
1. If you find the channel_type you're looking for, temporarily note it as a touple in a notepad somewhere with format `(ch_type_id, universal_library_repository)`. 
1. If you don't find it, make a new one. It's important to try and reduce the number of channel_types in here to reduce complexity, but it's also important that you adhere to strict and true rules about what is allowed to be mapped to what. Modifications and additions to this document should be taken and reviewed very seriously.

??? info "`chtype.path(channel_type)`"

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

??? info "`chtype.parse(val)`"

    Convert stored string into a tuple (chid:int, lib_repo:str).
    Handles both single tuples and extracts first tuple from lists.

??? info "`chtype.compatibles(channel_type)`"

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

??? info "`chtype.attribute(channel_type, attribute)`"

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

??? info "`chtype.signals(channel_type)`"

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

??? info "`chtype.is_or_is_compatible_with(channel_type)`"

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

