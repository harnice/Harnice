# import your modules here
import os
import subprocess
from harnice import fileio, state

# describe your args here. comment them out and do not officially define because they are called via runpy,
# for example, the caller feature_tree should define the arguments like this:
# feature_tree_utils.run_macro(
#    "kicad_sch_to_svg_no_nets",
#    "harness_artifacts",
#    "https://github.com/harnice/harnice-library-public",
#    artifact_id="kicad-schematic-svg-no-nets",
#    input_schematic="kicad/my_project.kicad_sch",
#    kicad_cli="kicad-cli",  # optional
# )
#
# Expected args (injected by caller or defaulted below):
# artifact_id: str (optional override)
# base_directory: str | None  (optional override)

# define the artifact_id of this macro (treated the same as part number). should match the filename.
artifact_id = "kicad_sch_net_overlay"

# =============== PATHS ===================================================================================
# this function does not need to be called in your macro, just by the default functions below.
# add your file structure inside here: keys are filenames, values are human-readable references. keys with contents are folder names.
# you can also add variables to the filenames, like example_variable_tofu. if you don't need to do this, you can delete references to tofu in this guide.
def macro_file_structure():
    # define the dictionary of the file structure of this macro
    return {
        f"{artifact_id}.log.txt": "kicad-cli export log",
        f"{artifact_id}-svgs.txt": "notes about exported svgs",
        "svgs": {}
    }

def file_structure():
    return {
        "kicad": {
            f"{state.partnumber('pn-rev')}.kicad_sch": "kicad sch",
        }
    }


# this runs automatically and is used to assign a default base directory if it is not called by the caller.
if base_directory == None:  # path between cwd and the file structure for this macro
    base_directory = os.path.join("instance_data", "macro", artifact_id)


# call this in your script to get the path to a file in this macro. it references logic from fileio but passes in the structure from this macro.
def path(target_value, example_variable_tofu=None):
    return fileio.path(
        target_value,
        structure_dict=macro_file_structure(),
        base_directory=base_directory,
        example_variable_tofu=example_variable_tofu,
        #
    )


def dirpath(target_value):
    # target_value = None will return the root of this macro
    return fileio.dirpath(
        target_value,
        structure_dict=macro_file_structure(),
        base_directory=base_directory,
    )


# don't forget to make the directories you've defined above.
os.makedirs(
    dirpath("svgs"),
    exist_ok=True,
)

# macro initialization complete. write the rest of the macro logic here.
# ==========================================================================================================

schematic_path = fileio.path("kicad sch", structure_dict=file_structure())

if not os.path.isfile(schematic_path):
    raise FileNotFoundError(
        f"Schematic not found. Check your kicad sch exists at this name and location: \n{schematic_path}"
    )

cmd = [
    "kicad-cli",
    "sch",
    "export",
    "svg",
    schematic_path,
    "-o",
    dirpath("svgs"),
]

subprocess.run(cmd, check=True, capture_output=True)
