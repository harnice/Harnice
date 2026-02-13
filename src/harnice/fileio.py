import os
import os.path
import datetime
import shutil
import re
import csv
import json
import subprocess
from harnice import state

# standard punctuation:
#  .  separates between name hierarchy levels
#  _  means nothing, basically a space character
#  -  if multiple instances are found at the same hierarchy level with the same name,
# this separates name from unique instance identifier


def part_directory():
    """Return the part directory: the parent of the current working directory.

When running in a revision folder (e.g. `mypart-rev1`), this is the part folder
(e.g. `mypart`). Equivalent to `os.path.dirname(os.getcwd())`.
    """
    return os.path.dirname(os.getcwd())


def rev_directory():
    """Return the current revision directory (the current working directory).

All product file-structure paths are resolved relative to this directory.
Same as `os.getcwd()`.
    """
    return os.getcwd()


def silentremove(filepath):
    """Remove a file or directory and its contents if it exists.

No-op if the path does not exist. Removes symlinks as files (does not follow).

**Args:**

- **filepath** — Path to the file or directory to remove.
    """
    if os.path.exists(filepath):
        if os.path.isfile(filepath) or os.path.islink(filepath):
            os.remove(filepath)  # remove file or symlink
        elif os.path.isdir(filepath):
            shutil.rmtree(filepath)  # remove directory and contents


def path(target_value, structure_dict=None, base_directory=None):
    """Return the full path to a file identified by its file key.

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

    """
    # FILES NOT DEPENDENT ON PRODUCT TYPE
    if target_value == "revision history":
        file_path = os.path.join(
            part_directory(), f"{state.partnumber('pn')}-revision_history.tsv"
        )
        return file_path

    # FILES DEPENDENT ON HARNICE ROOT

    if target_value == "library locations":
        import harnice

        harnice_root = os.path.dirname(
            os.path.dirname(os.path.dirname(harnice.__file__))
        )

        library_locations_path = os.path.join(harnice_root, "library_locations.csv")

        if not os.path.exists(library_locations_path):
            from harnice import cli

            answer = cli.prompt(
                f"Library locations file not found at {library_locations_path}. Create it?",
                default="y",
            )
            if answer.lower() not in ("y", "yes", ""):
                exit()

            with open(library_locations_path, "w") as f:
                f.write("repo_url,local_path\n")
                f.write(
                    f"https://github.com/harnice/harnice,{os.path.join(harnice_root, 'library_public')}\n"
                )

        return library_locations_path

    if target_value == "project locations":
        import harnice

        harnice_root = os.path.dirname(
            os.path.dirname(os.path.dirname(harnice.__file__))
        )
        project_locations_path = os.path.join(harnice_root, "project_locations.csv")
        if not os.path.exists(project_locations_path):
            from harnice import cli

            answer = cli.prompt(
                f"Project locations file not found at {project_locations_path}. Create it?",
                default="y",
            )
            if answer.lower() not in ("y", "yes", ""):
                exit()

            with open(project_locations_path, "w") as f:
                f.write("traceable_key,local_path\n")
                f.write("your project part number,local path to your project\n")

        return os.path.join(harnice_root, "project_locations.csv")

    if target_value == "drawnby":
        import harnice

        harnice_root = os.path.dirname(
            os.path.dirname(os.path.dirname(harnice.__file__))
        )

        drawnby_path = os.path.join(harnice_root, "drawnby.json")
        if not os.path.exists(drawnby_path):
            from harnice import cli

            answer = cli.prompt(
                f"Drawnby file not found at {drawnby_path}. Create it?", default="y"
            )
            if answer.lower() not in ("y", "yes", ""):
                exit()

            name = cli.prompt(
                "Enter your name: (recommended: first inital, last name, all caps: K SHUTT)"
            )

            while not name:
                print("Name cannot be empty. Please try again.")
                name = cli.prompt("Enter your name")

            with open(drawnby_path, "w") as f:
                f.write(f"{name}\n")

        return drawnby_path

    # FILES INSIDE OF A STRUCURE DEFINED BY FILEIO
    # look up from default structure state if not provided
    if structure_dict is None:
        structure_dict = state.file_structure

    def recursive_search(data, path):
        if isinstance(data, dict):
            for key, value in data.items():
                if value == target_value:
                    return path + [key]
                result = recursive_search(value, path + [key])
                if result:
                    return result
        elif isinstance(data, list):
            for index, item in enumerate(data):
                if item == target_value:
                    return path + [f"[{index}]"]
                result = recursive_search(item, path + [f"[{index}]"])
                if result:
                    return result
        return None

    path_value = recursive_search(structure_dict, [])

    if not path_value:
        raise TypeError(f"Could not find filepath of '{target_value}'.")
    if base_directory in [None, ""]:
        return os.path.join(rev_directory(), *path_value)
    else:
        return os.path.join(rev_directory(), base_directory, *path_value)


def dirpath(target_key, structure_dict=None, base_directory=None):
    """Return the full path to a directory identified by its key in the file structure.

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
    """
    if target_key == "rev directory":
        return rev_directory()

    if target_key == "part directory":
        return part_directory()

    if target_key is None:
        if base_directory in [None, ""]:
            return os.path.join(rev_directory())
        else:
            return os.path.join(rev_directory(), base_directory)

    if structure_dict is None:
        structure_dict = state.file_structure

    def recursive_search(data, path):
        if isinstance(data, dict):
            for key, value in data.items():
                # if the current key matches, return its path immediately
                if key == target_key:
                    return path + [key]
                # otherwise, keep descending
                result = recursive_search(value, path + [key])
                if result:
                    return result
        elif isinstance(data, list):
            for index, item in enumerate(data):
                result = recursive_search(item, path + [f"[{index}]"])
                if result:
                    return result
        return None

    path_key = recursive_search(structure_dict, [])
    if not path_key:
        raise TypeError(f"Could not find directory '{target_key}'.")
    if base_directory in [None, ""]:
        return os.path.join(rev_directory(), *path_key)
    else:
        return os.path.join(rev_directory(), base_directory, *path_key)


def verify_revision_structure():
    """Ensure the current directory is a valid revision folder and set `state.pn` and `state.rev`.

Called by the CLI before rendering.

**Behavior:**

- If cwd is a `<part>-rev<N>` folder: sets `state.pn` and `state.rev` from the path.
- If cwd is a part folder that contains rev folders: prints a message and exits.
- Otherwise: prompts to create a new PN here, creates the first rev folder, and `chdir` into it.

Ensures revision_history exists and that the revision status is blank (Harnice only
renders revisions with blank status). Updates revision_history datemodified.
    """
    from harnice import cli
    from harnice.lists import rev_history

    cwd = os.getcwd()
    cwd_name = os.path.basename(cwd)
    parent = os.path.basename(os.path.dirname(cwd))

    # --- 1) Already in a <PN>-revN folder? ---
    if cwd_name.startswith(f"{parent}-rev") and cwd_name.split("-rev")[-1].isdigit():
        state.set_pn(parent)
        state.set_rev(int(cwd_name.split("-rev")[-1]))

    # --- 2) In a part folder that contains revision folders? ---
    elif any(
        re.fullmatch(rf"{re.escape(cwd_name)}-rev\d+", d) for d in os.listdir(cwd)
    ):
        print(f"This is a part folder ({cwd_name}).")
        print(f"Please `cd` into a revision folder (e.g. `{cwd_name}-rev1`) and rerun.")
        exit()

    # --- 3) No revision structure → initialize new PN here ---
    else:
        answer = cli.prompt(
            f"No valid Harnice file structure detected in '{cwd_name}'. Create new PN here?",
            default="y",
        )
        if answer.lower() not in ("y", "yes", ""):
            exit()

        state.set_pn(cwd_name)

        # inline prompt_new_rev
        rev = int(cli.prompt("Enter revision number", default="1"))
        state.set_rev(rev)
        folder = os.path.join(cwd, f"{state.pn}-rev{state.rev}")
        os.makedirs(folder, exist_ok=True)
        os.chdir(folder)

    # --- Ensure revision_history entry exists ---
    try:
        rev_history.info()
    except ValueError:
        rev_history.append(next_rev=state.rev)
    except FileNotFoundError:
        rev_history.append(next_rev=state.rev)

    # --- Status must be blank to proceed ---
    if rev_history.info(field="status") != "":
        raise RuntimeError(
            f"Revision {state.rev} status is not clear. "
            f"Harnice only renders revisions with a blank status."
        )

    print(f"Rendering PN: {state.pn}, Rev: {state.rev}")
    rev_history.update_datemodified()


def today():
    """Return today's date as a short string: `M/D/YY` (e.g. `2/12/25`)."""
    d = datetime.date.today()
    return f"{d.month}/{d.day}/{d.year % 100}"


def get_git_hash_of_harnice_src():
    """Return the git commit hash of the Harnice source repo (HEAD).

Used for version/attribution in outputs. Returns `"UNKNOWN"` if git is
unavailable or the repo cannot be read.
    """
    try:
        # get path to harnice package directory
        import harnice

        repo_dir = os.path.dirname(os.path.dirname(harnice.__file__))
        # ask git for commit hash
        return (
            subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo_dir)
            .decode("utf-8")
            .strip()
        )
    except Exception:
        return "UNKNOWN"


def get_path_to_project(traceable_key):
    """Return the local filesystem path for a project identified by a traceable key.

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
    """
    from harnice import fileio

    path = fileio.path("project locations")  # resolves to project_locations.csv

    if not os.path.exists(path):
        raise FileNotFoundError(
            "Make a CSV at the root of your Harnice repo called project_locations.csv "
            "with the following format (no headers):\n\n"
            "    traceable_key,local_path\n"
        )

    traceable_key = traceable_key.strip()

    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter=",")
        for row in reader:
            # skip blank or comment lines
            if not row or len(row) < 2 or row[0].strip().startswith("#"):
                continue

            key, local = row[0].strip(), row[1].strip()

            if key == traceable_key:
                if not local:
                    raise ValueError(
                        f"No project local path found for '{traceable_key}'"
                    )
                return os.path.expanduser(local)

    raise ValueError(f"Could not find project traceable key '{traceable_key}'")


def read_tsv(filepath, delimiter="\t"):
    """Read a TSV file and return a list of row dicts (one dict per row, keys from header).

If **filepath** is an existing file path, that file is read. If not, **filepath** is
treated as a file key and `fileio.path(filepath)` is used to resolve the path
(e.g. `"instances list"` or `"signals list"`).

**Args:**

- **filepath** — Path to a TSV file, or a file key (e.g. `"instances list"`).
- **delimiter** — Column delimiter; default `"\\t"`.

**Returns:** List of dicts, one per data row, with keys from the header row (`list`).

**Raises:** `FileNotFoundError` if the path does not exist or the resolved path does not exist.
    """
    try:
        with open(filepath, newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f, delimiter=delimiter))
    except FileNotFoundError:
        filepath = path(filepath)
        try:
            with open(filepath, newline="", encoding="utf-8") as f:
                return list(csv.DictReader(f, delimiter=delimiter))
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Expected csv or tsv file with delimiter '{delimiter}' at path or key {filepath}"
            )


def drawnby():
    """Load and return the contents of the drawnby file (path from `fileio.path("drawnby")`).

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
    """
    return json.load(open(path("drawnby")))
