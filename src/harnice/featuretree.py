import os
import runpy
from harnice import fileio, component_library

def runprebuilder(prebuilder_name, supplier):
    destination_directory=os.path.join(fileio.dirpath("prebuilders"), prebuilder_name)
    os.makedirs(destination_directory, exist_ok=True)
    component_library.pull_item_from_library(
        supplier=supplier,
        lib_subpath="prebuilders",
        mpn=prebuilder_name,
        destination_directory=destination_directory,
        used_rev=None,
        item_name=prebuilder_name
    )

    #if prebuilder_name is something
        #make config files in the destination directory

    runpy.run_path(os.path.join(destination_directory, f"{prebuilder_name}.py"), run_name="__main__")


def runartifactbuilder(artifact_builder_name, supplier, artifact_id, scale=None, scales=None):
    destination_directory = os.path.join(fileio.dirpath("artifacts"), artifact_builder_name, artifact_id)
    os.makedirs(destination_directory, exist_ok=True)

    component_library.pull_item_from_library(
        supplier=supplier,
        lib_subpath="artifact_builders",
        mpn=artifact_builder_name,
        destination_directory=destination_directory,
        used_rev=None,
        item_name=artifact_builder_name
    )

    script_path = os.path.join(destination_directory, f"{artifact_builder_name}.py")

    # Variables to pass into the executed script
    init_globals = {
        "scale": scale,
        "scales": scales,
        "artifact_id": artifact_id
    }

    runpy.run_path(script_path, run_name="__main__", init_globals=init_globals)