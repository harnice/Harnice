import os
import runpy
import math
import json
import shutil
from harnice import fileio, library_utils
from harnice.lists import instances_list


def run_macro(macro_name, lib_subpath, lib_repo, artifact_id="", **kwargs):
    if artifact_id == "":
        macro_dirpath = os.path.join(
            fileio.dirpath("macros"), lib_subpath, f"{macro_name}"
        )
    else:
        macro_dirpath = os.path.join(
            fileio.dirpath("macros"), lib_subpath, f"{macro_name}-{artifact_id}"
        )
    os.makedirs(macro_dirpath, exist_ok=True)

    library_utils.pull_item_from_library(
        lib_repo=lib_repo,
        product="macros",
        lib_subpath=lib_subpath,
        mpn=macro_name,
        destination_directory=macro_dirpath,
        used_rev=None,
        item_name=macro_name,
    )

    script_path = os.path.join(macro_dirpath, f"{macro_name}.py")

    # always pass the basics, but let kwargs override/extend
    init_globals = {
        "artifact_id": artifact_id,
        "artifact_path": macro_dirpath,
        **kwargs,  # merges/overrides
    }

    runpy.run_path(script_path, run_name="__main__", init_globals=init_globals)


def lookup_outputcsys_from_lib_used(lib_name, outputcsys):
    attributes_path = os.path.join(
        fileio.dirpath("imported_instances"), lib_name, f"{lib_name}-attributes.json"
    )

    try:
        with open(attributes_path, "r", encoding="utf-8") as f:
            attributes_data = json.load(f)
    except (json.JSONDecodeError, IOError):
        return 0, 0, 0

    csys_children = attributes_data.get("csys_children", {})
    if outputcsys == "origin":
        return 0, 0, 0

    if outputcsys not in csys_children:
        raise ValueError(
            f"[ERROR] Output coordinate system '{outputcsys}' not found in {lib_name}-attributes.json"
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


def update_translate_content():
    # this looks through parent csys and finds its output csys and recommends its translate_x and translate_y
    for instance in fileio.read_tsv("instances list"):
        if instance.get("parent_csys_instance_name") in ["", None]:
            continue  # skip if there isn't a parent defined

        if instance.get("item_type") == "Node":
            continue  # these are automatically assigned at start

        parent_csys_outputcsys_name = instance.get("parent_csys_outputcsys_name")

        if not parent_csys_outputcsys_name:
            continue  # skip if missing required info

        x, y, rotation = lookup_outputcsys_from_lib_used(
            instance.get("parent_csys_instance_name"), parent_csys_outputcsys_name
        )

        instances_list.modify(
            instance.get("instance_name"),
            {"translate_x": x, "translate_y": y, "rotate_csys": rotation},
        )


def copy_pdfs_to_cwd():
    artifacts_dir = fileio.dirpath("macros")
    cwd = os.getcwd()

    for root, _, files in os.walk(artifacts_dir):
        for filename in files:
            if filename.lower().endswith(".pdf"):
                source_path = os.path.join(root, filename)
                dest_path = os.path.join(cwd, filename)

                try:
                    shutil.copy2(source_path, dest_path)  # preserves metadata
                except Exception as e:
                    print(f"[ERROR] Could not copy {source_path}: {e}")


def run_feature_for_relative(project_key, referenced_pn_rev, feature_tree_utils_name):
    project_path = fileio.get_path_to_project(project_key)
    feature_tree_utils_path = os.path.join(
        project_path,
        f"{referenced_pn_rev[0]}-{referenced_pn_rev[1]}",
        "features_for_relatives",
        feature_tree_utils_name,
    )
    runpy.run_path(feature_tree_utils_path, run_name="__main__")
