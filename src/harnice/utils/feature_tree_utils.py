import os
import runpy
import math
import json
import shutil
from harnice import fileio
from harnice.utils import library_utils


def run_macro(
    macro_part_number, lib_subpath, lib_repo, artifact_id, base_directory=None, **kwargs
):
    """
    Runs a macro script from the library with the given artifact ID.

    Imports a macro from the library and executes its Python script. The macro
    is pulled into a directory structure and then executed with the `artifact_id`
    and any additional keyword arguments passed as global variables.

    **Args:**
    - `macro_part_number` (str): Part number of the macro to run.
    - `lib_subpath` (str): Library subpath where the macro is located.
    - `lib_repo` (str): Library repository URL or `"local"` for local library.
    - `artifact_id` (str): Unique identifier for this macro execution (must be unique).
    - `base_directory` (str, optional): Base directory for the macro output. If `None`,
        defaults to `instance_data/macro/{artifact_id}`.
    - `**kwargs`: Additional keyword arguments to pass as global variables to the macro script.

    **Raises:**
    - `ValueError`: If `artifact_id` is `None`, `macro_part_number` is `None`, `lib_repo` is `None`,
        or if a macro with the given `artifact_id` already exists in library history.
    """
    if artifact_id is None:
        raise ValueError("artifact_id is required")
    if macro_part_number is None:
        raise ValueError("macro_part_number is required")
    if lib_repo is None:
        raise ValueError("lib_repo is required")

    for instance in fileio.read_tsv("library history"):
        if instance.get("instance_name") == artifact_id:
            raise ValueError(f"Macro with ID {artifact_id} already exists")

    if base_directory is None:
        base_directory = os.path.join("instance_data", "macro", artifact_id)

    os.makedirs(fileio.dirpath(None, base_directory), exist_ok=True)

    library_utils.pull(
        {
            "mpn": macro_part_number,
            "lib_repo": lib_repo,
            "lib_subpath": lib_subpath,
            "item_type": "macro",
            "instance_name": artifact_id,
        },
        destination_directory=fileio.dirpath(None, base_directory=base_directory),
        update_instances_list=False,
    )

    script_path = os.path.join(
        fileio.dirpath(None, base_directory=base_directory), f"{macro_part_number}.py"
    )

    # always pass the basics, but let kwargs override/extend
    init_globals = {
        "artifact_id": artifact_id,
        "artifact_path": base_directory,
        "base_directory": base_directory,
        **kwargs,  # merges/overrides
    }

    runpy.run_path(script_path, run_name="__main__", init_globals=init_globals)


def lookup_outputcsys_from_lib_used(instance, outputcsys, base_directory=None):
    """
    Looks up coordinate system transform from an instance's library attributes.

    Reads the instance's attributes JSON file to find the specified output coordinate
    system definition and returns its transform values. If the coordinate system is
    `"origin"`, returns zero transform.

    **Args:**
    - `instance` (dict): Instance dictionary containing `item_type` and `instance_name`.
    - `outputcsys` (str): Name of the output coordinate system to look up (`"origin"` returns zero transform).
    - `base_directory` (str, optional): Base directory path. If `None`, uses current working directory.

    **Returns:**
    - `tuple`: A tuple of `(x, y, rotation)` representing the coordinate system transform.
        Returns `(0, 0, 0)` if the coordinate system is `"origin"` or if the attributes
        file is not found.

    **Raises:**
    - `ValueError`: If the specified output coordinate system is not defined in the
        instance's attributes file.
    """
    if outputcsys == "origin":
        return 0, 0, 0

    attributes_path = os.path.join(
        fileio.dirpath(None, base_directory=base_directory),
        "instance_data",
        instance.get("item_type"),
        instance.get("instance_name"),
        f"{instance.get('instance_name')}-attributes.json",
    )

    try:
        with open(attributes_path, "r", encoding="utf-8") as f:
            attributes_data = json.load(f)
    except FileNotFoundError:
        return 0, 0, 0

    csys_children = attributes_data.get("csys_children", {})

    if outputcsys not in csys_children:
        raise ValueError(
            f"[ERROR] Output coordinate system '{outputcsys}' not defined in {attributes_path}"
        )

    child_csys = csys_children[outputcsys]

    # Extract values with safe numeric defaults
    x = child_csys.get("x", 0)
    y = child_csys.get("y", 0)
    angle = child_csys.get("angle", 0)
    distance = child_csys.get("distance", 0)
    rotation = child_csys.get("rotation", 0)

    # Convert angle to radians if it's stored in degrees
    angle_rad = math.radians(angle)

    # Apply translation based on distance + angle
    x = x + distance * math.cos(angle_rad)
    y = y + distance * math.sin(angle_rad)

    return x, y, rotation


def copy_pdfs_to_cwd():
    """
    Copies all PDF files from `instance_data` directory to the current working directory.

    Recursively searches the `instance_data` directory tree and copies all PDF files
    found to the current working directory. Preserves file metadata during copy.
    Prints error messages if any files cannot be copied but continues processing.
    """
    cwd = os.getcwd()

    for root, _, files in os.walk(fileio.dirpath(None, base_directory="instance_data")):
        for filename in files:
            if filename.lower().endswith(".pdf"):
                source_path = os.path.join(root, filename)
                dest_path = os.path.join(cwd, filename)

                try:
                    shutil.copy2(source_path, dest_path)  # preserves metadata
                except Exception as e:
                    print(f"[ERROR] Could not copy {source_path}: {e}")


def run_feature_for_relative(project_key, referenced_pn_rev, feature_tree_utils_name):
    """
    Runs a feature tree script from a referenced part's `features_for_relatives` directory.

    Executes a Python script located in the `features_for_relatives` directory of a
    referenced part. This is used to run feature scripts that are associated with
    parts referenced by the current project.

    **Args:**
    - `project_key` (str): Key identifying the project to look up.
    - `referenced_pn_rev` (tuple): Tuple of `(part_number, revision)` for the referenced part.
    - `feature_tree_utils_name` (str): Filename of the feature tree script to execute.
    """
    project_path = fileio.get_path_to_project(project_key)
    feature_tree_utils_path = os.path.join(
        project_path,
        f"{referenced_pn_rev[0]}-{referenced_pn_rev[1]}",
        "features_for_relatives",
        feature_tree_utils_name,
    )
    runpy.run_path(feature_tree_utils_path, run_name="__main__")


def default_feature_tree_contents(filename, replacements=None):

    path = os.path.join(fileio.harnice_root(), "src", "harnice", "default_product_feature_trees", filename)

    with open(path, "r") as f:
        content = f.read()

    if replacements:
        for key, value in replacements.items():
            content = content.replace("{key}", value)
            
    return content