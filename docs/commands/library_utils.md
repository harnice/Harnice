# Library Utilities
---
##Commands:
*Use the following functions by first importing the module in your script like this: 
```python
from harnice.lists import library_utils
```
 then use as written.*
??? info "`library_utils.pull()`"

    Imports a part from the library into the project.
    
    Copies a part (device, connector, cable, etc.) from the library repository into
    the project's `instance_data` directory. Handles revision selection, file copying,
    and updating the instances list and library history. The function:
    
    1. Validates required fields (`lib_repo`, `mpn`, `item_type`)
    2. Determines which revision to use (specified or latest available)
    3. Copies the library revision to `library_used_do_not_edit`
    4. Copies editable files to the instance directory (only if not already present)
    5. Updates the instances list with library metadata
    6. Records the import in library history
    
    **Args:**
    - `input_dict` (dict): Dictionary containing part information with required keys:
        - `instance_name` (str): Name for this instance in the project
        - `lib_repo` (str): Library repository URL or `"local"` for local library
        - `mpn` (str): Manufacturer part number
        - `item_type` (str): Type of item (device, connector, cable, etc.)
        - `lib_subpath` (str, optional): Subpath within the library
        - `lib_rev_used_here` (str, optional): Specific revision to use (e.g., `"1"` or `"rev1"`)
    - `update_instances_list` (bool, optional): If `True`, updates the instances list with
        library metadata. Defaults to `True`.
    - `destination_directory` (str, optional): Custom destination directory. If `None`,
        defaults to `instance_data/{item_type}/{instance_name}`.
    
    **Returns:**
    - `str`: Path to the destination directory where the part was imported.
    
    **Raises:**
    - `ValueError`: If required fields (`lib_repo`, `mpn`, `item_type`) are blank.
    - `FileNotFoundError`: If no revision folders are found for the part number in the library.

??? info "`library_utils.get_local_path()`"

    Looks up the local filesystem path for a library repository URL.
    
    Reads the `library_locations.csv` file to find the mapping between a library
    repository URL and its local filesystem path. If the CSV file doesn't exist,
    it creates one with a default entry for the `harnice-library-public` repository.
    
    The lookup is case-insensitive. The local path is expanded (e.g., `~` is expanded
    to the user's home directory).
    
    **Args:**
    - `lib_repo` (str): Library repository URL to look up (e.g., 
        `"https://github.com/harnice/harnice-library-public"`).
    
    **Returns:**
    - `str`: Local filesystem path to the library repository.
    
    **Raises:**
    - `ValueError`: If the library repository URL is not found in the CSV file,
        or if no local path is specified for the repository.

