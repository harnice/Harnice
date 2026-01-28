# Macros

---

## New Macros: Start Here

You can copy and paste this template into your new macro (or ai tool lol) to form the structure of your macro.
```python
# import your modules here

# describe your args here. comment them out and do not officially define because they are called via runpy, 
# for example, the caller feature_tree should define the arguments like this:
# feature_tree_utils.run_macro(
#    "standard_harnice_formboard",
#    "harness_artifacts",
#    "https://github.com/harnice/harnice",
#    artifact_id="formboard-overview",
#    scale=scales.get("A"),
#    input_instances=formboard_overview_instances,
# )

# define the artifact_id of this macro (treated the same as part number). should match the filename.
artifact_id = "example_macro"

# =============== PATHS ===================================================================================
# this function does not need to be called in your macro, just by the default functions below.
# add your file structure inside here: keys are filenames, values are human-readable references. keys with contents are folder names.
# you can also add variables to the filenames, like example_variable_tofu. if you don't need to do this, you can delete references to tofu in this guide.
def macro_file_structure(example_variable_tofu=None):
    # define the dictionary of the file structure of this macro
    return {
        f"{artifact_id}-example.txt": "text file",
        "folder": {
            f"{artifact_id}-{example_variable_tofu}.csv": "csv file",
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
    dirpath("folder"),
    exist_ok=True,
)

# macro initialization complete. write the rest of the macro logic here. there are no remaining required functions to call.
# ==========================================================================================================
```
