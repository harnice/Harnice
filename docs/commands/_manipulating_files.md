# Keeping Track of Files

The `fileio` module keeps files organized! With the tools described in this page, you should never need to reference a file by constructing a path from scratch.

## Part number and revision folders

Harnice requires a revision folder and a part number folder to be able to render any product.

```python
# suppose your part number is "123456" and your revision is "A"

|-- A123456/
    L--   A123456-revA/
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

    Return the full path to a file identified by its file key.
    
    * file structure dict (`state.file_structure`, or **structure_dict** if provided) is searched for a *value* equal to **target_value**. The path is built from the rev directory + **base_directory** (if any) + the key path to that value.
    
    **Special Target Values:**
    
    - **`revision history`:** the revision history file of the product you're currently working on
    - **`library locations`:** the library locations file on your computer
    - **`project locations`:** the project locations file on your computer
    - **`drawnby`:** the text file on your computer that stores your name
    - **`rev directory`:** the revsion directory of the product you're currently working on
    - **`part directory`:** the part directory of the product you're currently working on
    
    **Args:**
    
    - **target_value** — File key to look up (e.g. `"signals list"`, `"feature tree"`).
    - **structure_dict** — Optional. Override the default structure (e.g. for a macro).
        If `None`, uses `state.file_structure`.
    - **base_directory** — Optional. Subdirectory under the rev directory to use as
        the root for structure paths. If `None` or `""`, paths are under the rev directory only.
    
    **Returns:** Absolute path to the file (`str`).
    
    **Raises:** `TypeError` if **target_value** is not found in the structure (for non-special keys).
    
    **CLI interactions**
    - If `library locations`, `project locations`, or `drawnby` files do not exist on your computer (maybe this is a newly run install?) the CLI will prompt you to create the default csv's in the correct location.

??? info "`fileio.dirpath(target_key, structure_dict=None, base_directory=None)`"

    Return the full path to a directory identified by its key in the file structure.
    
    Searches the file structure (`state.file_structure` or **structure_dict**) for a
    *key* equal to **target_key** (directory names are keys; file keys are values).
    The path is built from the rev directory + **base_directory** (if any) + the path to that key.
    
    **Special Target Keys:**
    
    - **`part directory`:** part directory of the product you're currently working on
    - **`rev directory`:** rev directory of the product you're currently working on
    
    **Args:**
    
    - **target_key** — Directory name in the structure (e.g. `"lists"`, `"maps"`).
        Pass `None` to get the rev directory (or rev + **base_directory**).
    - **structure_dict** — Optional. Override the default structure. If `None`, uses `state.file_structure`.
    - **base_directory** — Optional. Subdirectory under the rev directory. If `None` or `""`,
        paths are under the rev directory only.
    
    **Returns:** Absolute path to the directory (`str`).
    
    **Raises:** `TypeError` if **target_key** is not `None` and not found in the structure.



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

    Return the current part number and/or revision in the requested format.
    
    Assumes `state.pn` and `state.rev` are set (e.g. by `fileio.verify_revision_structure()`).
    For a part `"mypart"` and rev `1`:
    
    **Args:**
    
    - **format** — One of:
        - `"pn-rev"`: full part-rev string, e.g. `"mypart-rev1"`
        - `"pn"`: part number only, e.g. `"mypart"`
        - `"rev"`: revision label, e.g. `"rev1"`
        - `"R"`: revision number only, e.g. `"1"`
    
    **Returns:** The requested substring of `"pn-revRev"` (e.g. `"mypart-rev1"`) (`str`).
    
    **Raises:** `ValueError` if **format** is not one of the options above.


---
##Commands:
*Use the following functions by first importing the module in your script like this: 
```python
from harnice.lists import fileio
```
 then use as written.*
??? info "`state.partnumber(format)`"

    Return the current part number and/or revision in the requested format.
    
    Assumes `state.pn` and `state.rev` are set (e.g. by `fileio.verify_revision_structure()`).
    For a part `"mypart"` and rev `1`:
    
    **Args:**
    
    - **format** — One of:
        - `"pn-rev"`: full part-rev string, e.g. `"mypart-rev1"`
        - `"pn"`: part number only, e.g. `"mypart"`
        - `"rev"`: revision label, e.g. `"rev1"`
        - `"R"`: revision number only, e.g. `"1"`
    
    **Returns:** The requested substring of `"pn-revRev"` (e.g. `"mypart-rev1"`) (`str`).
    
    **Raises:** `ValueError` if **format** is not one of the options above.

??? info "`fileio.path(target_value, structure_dict=None, base_directory=None)`"

    Return the full path to a file identified by its file key.
    
    * file structure dict (`state.file_structure`, or **structure_dict** if provided) is searched for a *value* equal to **target_value**. The path is built from the rev directory + **base_directory** (if any) + the key path to that value.
    
    **Special Target Values:**
    
    - **`revision history`:** the revision history file of the product you're currently working on
    - **`library locations`:** the library locations file on your computer
    - **`project locations`:** the project locations file on your computer
    - **`drawnby`:** the text file on your computer that stores your name
    - **`rev directory`:** the revsion directory of the product you're currently working on
    - **`part directory`:** the part directory of the product you're currently working on
    
    **Args:**
    
    - **target_value** — File key to look up (e.g. `"signals list"`, `"feature tree"`).
    - **structure_dict** — Optional. Override the default structure (e.g. for a macro).
        If `None`, uses `state.file_structure`.
    - **base_directory** — Optional. Subdirectory under the rev directory to use as
        the root for structure paths. If `None` or `""`, paths are under the rev directory only.
    
    **Returns:** Absolute path to the file (`str`).
    
    **Raises:** `TypeError` if **target_value** is not found in the structure (for non-special keys).
    
    **CLI interactions**
    - If `library locations`, `project locations`, or `drawnby` files do not exist on your computer (maybe this is a newly run install?) the CLI will prompt you to create the default csv's in the correct location.

??? info "`fileio.dirpath(target_key, structure_dict=None, base_directory=None)`"

    Return the full path to a directory identified by its key in the file structure.
    
    Searches the file structure (`state.file_structure` or **structure_dict**) for a
    *key* equal to **target_key** (directory names are keys; file keys are values).
    The path is built from the rev directory + **base_directory** (if any) + the path to that key.
    
    **Special Target Keys:**
    
    - **`part directory`:** part directory of the product you're currently working on
    - **`rev directory`:** rev directory of the product you're currently working on
    
    **Args:**
    
    - **target_key** — Directory name in the structure (e.g. `"lists"`, `"maps"`).
        Pass `None` to get the rev directory (or rev + **base_directory**).
    - **structure_dict** — Optional. Override the default structure. If `None`, uses `state.file_structure`.
    - **base_directory** — Optional. Subdirectory under the rev directory. If `None` or `""`,
        paths are under the rev directory only.
    
    **Returns:** Absolute path to the directory (`str`).
    
    **Raises:** `TypeError` if **target_key** is not `None` and not found in the structure.

??? info "`fileio.silentremove(filepath)`"

    Remove a file or directory and its contents if it exists.
    
    No-op if the path does not exist. Removes symlinks as files (does not follow).
    
    **Args:**
    
    - **filepath** — Path to the file or directory to remove.

??? info "`fileio.get_git_hash_of_harnice_src()`"

    Return the git commit hash of the Harnice source repo (HEAD).
    
    Used for version/attribution in outputs. Returns `"UNKNOWN"` if git is
    unavailable or the repo cannot be read.

??? info "`fileio.get_path_to_project(traceable_key)`"

    Return the local filesystem path for a project identified by a traceable key.
    
    Reads `project_locations.csv` (at `fileio.path("project locations")`) and returns
    the expanded local path for the row whose **traceable_key** matches. Used to
    resolve paths to systems, libraries, or other projects by part number or URL.
    
    **Args:**
    
    - **traceable_key** — Key to look up (e.g. part number or project identifier).
        Leading/trailing whitespace is stripped.
    
    **Returns:** `os.path.expanduser(local_path)` for the matching row (`str`).
    
    **Raises:**
    
    - `FileNotFoundError` — If `project_locations.csv` does not exist.
    - `ValueError` — If **traceable_key** is not found or has no local path.

??? info "`fileio.read_tsv(filepath, delimiter='\t')`"

    Read a TSV file and return a list of row dicts (one dict per row, keys from header).
    
    If **filepath** is an existing file path, that file is read. If not, **filepath** is
    treated as a file key and `fileio.path(filepath)` is used to resolve the path
    (e.g. `"instances list"` or `"signals list"`).
    
    **Args:**
    
    - **filepath** — Path to a TSV file, or a file key (e.g. `"instances list"`).
    - **delimiter** — Column delimiter; default `"\t"`.
    
    **Returns:** List of dicts, one per data row, with keys from the header row (`list`).
    
    **Raises:** `FileNotFoundError` if the path does not exist or the resolved path does not exist.

??? info "`fileio.drawnby()`"

    Load and return the contents of the drawnby file (path from `fileio.path("drawnby")`).
    
    The drawnby file lives at the Harnice repo root and stores author/credits info.
    
    That file should be structured like this, and this function will return exactly the same as a json object:
    ```json
    {
        "name": "K SHUTT"
    }
    ```
    Use case:
    ```python
    name = fileio.drawnby().get("name")
    ```

??? info "`fileio.today()`"

    Return today's date as a short string: `M/D/YY` (e.g. `2/12/25`).

This one happens behind the scenes, but here's how it knows you're in the right folder structure:

??? info "`fileio.verify_revision_structure()`"

    Ensure the current directory is a valid revision folder and set `state.pn` and `state.rev`.
    
    Called by the CLI before rendering.
    
    **Behavior:**
    
    - If cwd is a `<part>-rev<N>` folder: sets `state.pn` and `state.rev` from the path.
    - If cwd is a part folder that contains rev folders: prints a message and exits.
    - Otherwise: prompts to create a new PN here, creates the first rev folder, and `chdir` into it.
    
    Ensures revision_history exists and that the revision status is blank (Harnice only
    renders revisions with blank status). Updates revision_history datemodified.

