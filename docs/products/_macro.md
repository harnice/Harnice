# Macros

---

## New Macros: Start Here

You can copy and paste this template into your new macro (or ai tool) to form the structure of your macro.
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
# Harnice Macros

Macros are less fundamental commands, are revision controlled like parts, and offer a way for the user to call several instances while modifying each one slightly within your project.


A macro is a chunk of Python that has access to your project files or any other Python-capable function

When you call featuretree_utils.run_macro(), it will import the macro from a library and run it in your script

Some macros are designed to be used to build systems, build harnesses, or export contents “artifacts” from a harness instances list


# Build Macros

Intended to add or modify lines on an instances list based on a standard set of rules or instructions
Can read information from the instances list
Can read information from other support files
Examples
featuretree.runmacro(“import_wireviz_yaml”, “public”)
Reads a wireviz YAML (another commonly used harness design format)
featuretree. runmacro(“add_yellow_htshrk_to_plugs”, “kenyonshutt”)
You can write any rule or set of rules you want in Python, save it to your library, and call it from a harness feature tree.
This one, for example, might scour the instances list:
for plug in instances_list:
if item_type==plug:
instances_list.add(heatshrink, to cable near plug)


# Output Macros
Output Macros will scour the Instances List or other artifact outputs and make other things out of it
BOM
Formboard arrangement
PDF drawing sheet
Analysis calcs
Write your own!
    

## File Structure

Reference the files in your product by calling `fileio.path("file key")` from your script. They'll automatically use this structure:

```
fileio.dirpath("part_directory")       |-- yourpn/
                                           |-- earlier revs/
fileio.path("revision history")            |-- revhistory.csv
fileio.dirpath("rev_directory")            L-- your rev/
```
