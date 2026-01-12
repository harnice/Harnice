# Feature Tree Utilities
---
##Commands:
*Use the following functions by first importing the module in your script like this: 
```python
from harnice.lists import feature_tree_utils
```
 then use as written.*
??? info "`feature_tree_utils.run_macro()`"

    Runs a macro script from the library with the given artifact ID.
    
    Imports a macro from the library and executes its Python script. The macro
    is pulled into a directory structure and then executed with the artifact_id
    and any additional keyword arguments passed as global variables.
    
    Args:
        macro_part_number (str): Part number of the macro to run.
        lib_subpath (str): Library subpath where the macro is located.
        lib_repo (str): Library repository URL or "local" for local library.
        artifact_id (str): Unique identifier for this macro execution (must be unique).
        base_directory (str, optional): Base directory for the macro output. If None,
            defaults to instance_data/macro/{artifact_id}.
        **kwargs: Additional keyword arguments to pass as global variables to the macro script.
    
    Raises:
        ValueError: If artifact_id is None, macro_part_number is None, lib_repo is None,
            or if a macro with the given artifact_id already exists in library history.

??? info "`feature_tree_utils.lookup_outputcsys_from_lib_used()`"

    Looks up coordinate system transform from an instance's library attributes.
    
    Reads the instance's attributes JSON file to find the specified output coordinate
    system definition and returns its transform values. If the coordinate system is
    "origin", returns zero transform.
    
    Args:
        instance (dict): Instance dictionary containing item_type and instance_name.
        outputcsys (str): Name of the output coordinate system to look up ("origin" returns zero transform).
        base_directory (str, optional): Base directory path. If None, uses current working directory.
    
    Returns:
        tuple: A tuple of (x, y, rotation) representing the coordinate system transform.
            Returns (0, 0, 0) if the coordinate system is "origin" or if the attributes
            file is not found.
    
    Raises:
        ValueError: If the specified output coordinate system is not defined in the
            instance's attributes file.

??? info "`feature_tree_utils.copy_pdfs_to_cwd()`"

    Copies all PDF files from instance_data directory to the current working directory.
    
    Recursively searches the instance_data directory tree and copies all PDF files
    found to the current working directory. Preserves file metadata during copy.
    Prints error messages if any files cannot be copied but continues processing.

??? info "`feature_tree_utils.run_feature_for_relative()`"

    Runs a feature tree script from a referenced part's features_for_relatives directory.
    
    Executes a Python script located in the features_for_relatives directory of a
    referenced part. This is used to run feature scripts that are associated with
    parts referenced by the current project.
    
    Args:
        project_key (str): Key identifying the project to look up.
        referenced_pn_rev (tuple): Tuple of (part_number, revision) for the referenced part.
        feature_tree_utils_name (str): Filename of the feature tree script to execute.

