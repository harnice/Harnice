# Channel Types

---

## How are channels mapped?

---

## How to define a new channel type
1. In a repository of your choice (or start with [harnice_library_public](https://github.com/harnice/harnice) on your own branch), navigate to `library_repo/channel_types/channel_types.csv`
1. If you want channel definitions to be private and are therefore working in a private repository, ensure the repo's path is listed in file `library_locations.csv` (located at root of your harnice source code repo). The first column is the URL or traceable path, and the second column is your local path.
1. If you find the channel_type you're looking for, temporarily note it as a touple in a notepad somewhere with format `(ch_type_id, universal_library_repository)`. 
1. If you don't find it, make a new one. It's important to try and reduce the number of channel_types in here to reduce complexity, but it's also important that you adhere to strict and true rules about what is allowed to be mapped to what. Modifications and additions to this document should be taken and reviewed very seriously.

??? info "`chtype.parse(val)`"

    Convert stored string into a tuple (chid:int, lib_repo:str).
    Handles both single tuples and extracts first tuple from lists.

??? info "`chtype.compatibles(channel_type)`"

    Look up compatible channel_types for the given channel_type.
    Expects compatible_channel_types column to contain AST-parseable format:
    - Single tuple: (1, 'library_repo')
    - List of tuples: [(1, 'library_repo'), (2, 'library_repo')]

??? info "`chtype.attribute(channel_type, attribute)`"

    If you've defined other columns in your channel type, this will return that
    
    **Args**
    
     - `channel_type` standard touple-format
     - `attribute` header name of the attribute you need to find

