import os
import runpy
import math
import json
import shutil
from harnice import fileio, component_library, instances_list

def runprebuilder(prebuilder_name, supplier, **kwargs):
    destination_directory = os.path.join(fileio.dirpath("prebuilders"), prebuilder_name)
    os.makedirs(destination_directory, exist_ok=True)

    component_library.pull_item_from_library(
        supplier=supplier,
        lib_subpath="prebuilders",
        mpn=prebuilder_name,
        destination_directory=destination_directory,
        used_rev=None,
        item_name=prebuilder_name,
    )

    script_path = os.path.join(destination_directory, f"{prebuilder_name}.py")

    # forward **kwargs into the run context
    runpy.run_path(script_path, run_name="__main__", init_globals=kwargs)


def runartifactbuilder(artifact_builder_name, supplier, artifact_id, **kwargs):
    artifact_path = os.path.join(fileio.dirpath("artifacts"), f"{artifact_builder_name}-{artifact_id}")
    os.makedirs(artifact_path, exist_ok=True)

    component_library.pull_item_from_library(
        supplier=supplier,
        lib_subpath="artifact_builders",
        mpn=artifact_builder_name,
        destination_directory=artifact_path,
        used_rev=None,
        item_name=artifact_builder_name,
    )

    script_path = os.path.join(artifact_path, f"{artifact_builder_name}.py")

    # always pass the basics, but let kwargs override/extend
    init_globals = {
        "artifact_id": artifact_id,
        "artifact_path": artifact_path,
        **kwargs,  # merges/overrides
    }

    runpy.run_path(script_path, run_name="__main__", init_globals=init_globals)


def lookup_outputcsys_from_lib_used(lib_name, outputcsys):
    attributes_path = os.path.join(
        fileio.dirpath("imported_instances"),
        lib_name,
        f"{lib_name}-attributes.json"
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
    for instance in instances_list.read_instance_rows():

        if instance.get("parent_csys_instance_name") in ["", None]:
            continue # skip if there isn't a parent defined

        if instance.get("item_type") == "Node":
            continue # these are automatically assigned at start

        parent_csys_outputcsys_name = instance.get("parent_csys_outputcsys_name")

        if not parent_csys_outputcsys_name:
            continue  # skip if missing required info

        x, y, rotation = lookup_outputcsys_from_lib_used(instance.get("parent_csys_instance_name"), parent_csys_outputcsys_name)

        instances_list.modify(instance.get("instance_name"), {
            "translate_x": x,
            "translate_y": y,
            "rotate_csys": rotation
        })

def copy_pdfs_to_cwd():
    artifacts_dir = fileio.dirpath("artifacts")
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