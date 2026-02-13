# Keeping Track of Files

The `fileio` module keeps files organized! With the tools described in this page, you should never need to reference a file by constructing a path from scratch.

## Part number and revision folders

Harnice requires a revision folder and a part number folder to be able to render any product.

```python
# suppose your part number is "123456" and your revision is "A"

A123456/
   A123456-revA
```

If you're starting a new product, just make a new part number folder, run `harnice -r` from that folder in the command line, and the command line will help you build the right structure. 

Revision history data will be stored automatically inside the part number folder. That is the file that tells Harnice what kind of product you're currently working on, among other things. 

If you need to make a new revision of a product, navigate to a part or a rev folder in your command line, then enter `harnice --newrev`.

## Product file structures

Products and macros have their own pre-defined **file structure**. It's stored as a function inside the Harnice source code. Here's an example of the **Harness** one:

```python
def file_structure(): # example of a file structure of a product
    return {
        f"{state.partnumber('pn-rev')}-feature_tree.py": "feature tree",
        f"{state.partnumber('pn-rev')}-instances_list.tsv": "instances list",
        f"{state.partnumber('pn-rev')}-formboard_graph_definition.png": "formboard graph definition png",
        f"{state.partnumber('pn-rev')}-library_import_history.tsv": "library history",
        "interactive_files": {
            f"{state.partnumber('pn-rev')}.formboard_graph_definition.tsv": "formboard graph definition",
        },
    }
```

A file structure is defined for each product or macro. It is automatically passed into the code when that product or macro is ran. 

Here's the basics of how to read a file structure dictionary:

- **Files**: each file is a key–value pair where the **key** is the filename and the **value** is a short, human-readable **file key** (e.g. `"myfile.tsv": "signals list"`). You use the file key with `fileio.path("signals list")`.
- **Directories**: a directory is a key whose **value** is another dict (empty `{}` or more key–value pairs). The **key** is the directory name and is what you pass to `fileio.dirpath("dirname")`.

## Quick-start: accessing default files


??? info "`fileio.path(target_value, structure_dict=None, base_directory=None)`"

    Recursively searches for a value in a nested JSON structure and returns the path to the element containing that value.
    
    It's complicated ... check out https://harnice.io/commands/fileio/ for more information.
    
    Args:
        target_value (str): The value to search for.
    
    Returns:
        list: A list of container names leading to the element containing the target value, or None if not found.

??? info "`fileio.dirpath(target_key, structure_dict=None, base_directory=None)`"

    Returns the absolute path to a directory identified by its key
    within a dict hierarchy.



Use these two functions to access fils of any product. For most purposes, you can omit `structure_dict` and `base_directory`.

## The other arguments in `fileio.path()` and `fileio.dirpath()`

You can see from the above two functions that there are two optional arguments: `structure_dict` and `base_directory`. Here's what those mean:

**`structure_dict`:**

 - This is the file structure dictionary that is actually parsed to find the file path.
 - By default, the file structure of the product that's currently being run by Harnice is passed in at runtime.
 - Alternatively, if you need to pass a special structure dict in, you can do that here. You can do this, for example, if you have a custom macro or a custom file structure preference for an existing product.

**`base_directory`:**

 - This is the directory from which the relative paths from the file structure dictionary originates. 
 - By default, this is set to the revision folder of the product you're working on. This means that the file structure dictionary of the product is in reference to, or added on top of, the revision file of the current product.
 - If you need to reference files in another project, for example, or recursively with a macro that's called as an instance, that has its own sub-instances, you can change the base directory of the file structure dictionary to point to wherever you want with this. 

## Parametric file names in your folder structure

You can add extra arguments to `file_structure()` (and pass a custom dict into fileio) for more complex layouts. For example, maybe you need a filename that is controlled by a variable, like in this example:

```python
def macro_file_structure(page_name=None, page_counter=None):
    return {
        f"{state.partnumber('pn-rev')}-{artifact_id}-page_setup.json": "page setup",
        f"{artifact_id}-mastercontents.svg": "master contents svg",
        f"{state.partnumber('pn-rev')}-{artifact_id}.pdf": "output pdf",
        "page_svgs": {
            f"{page_counter}-{page_name}-user-editable.svg": "user editable page svg"
        },
    }
```

## Accessing the current part number and rev

Behind the scenes, Harnice stores the current part number and revision number in the module `state`. You can query it in any format you may need. 

??? info "`state.partnumber(format)`"

    Documentation needed.


---
##Commands:
*Use the following functions by first importing the module in your script like this: 
```python
from harnice.lists import <module 'harnice.fileio' from '/Users/kenyonshutt/Documents/GitHub/Harnice/src/harnice/fileio.py'>
```
 then use as written.*
??? info "`state.partnumber(format)`"

    Documentation needed.

??? info "`fileio.path(target_value, structure_dict=None, base_directory=None)`"

    Recursively searches for a value in a nested JSON structure and returns the path to the element containing that value.
    
    It's complicated ... check out https://harnice.io/commands/fileio/ for more information.
    
    Args:
        target_value (str): The value to search for.
    
    Returns:
        list: A list of container names leading to the element containing the target value, or None if not found.

??? info "`fileio.dirpath(target_key, structure_dict=None, base_directory=None)`"

    Returns the absolute path to a directory identified by its key
    within a dict hierarchy.

??? info "`fileio.silentremove(filepath)`"

    Removes a file or directory and its contents.
    
    Args:
        filepath (str): The path to the file or directory to remove.

??? info "`fileio.get_git_hash_of_harnice_src()`"

    Documentation needed.

??? info "`fileio.get_path_to_project(traceable_key)`"

    Given a traceable identifier for a project (PN, URL, etc),
    return the expanded local filesystem path.
    
    Expects a CSV at the root of the repo named:
        project_locations.csv
    
    Format (no headers):
        traceable_key,local_path

??? info "`fileio.read_tsv(filepath, delimiter='\t')`"

    Documentation needed.

??? info "`fileio.drawnby()`"

    Documentation needed.

This one happens behind the scenes, but here's how it knows you're in the right folder structure:

??? info "`fileio.verify_revision_structure()`"

    Documentation needed.

