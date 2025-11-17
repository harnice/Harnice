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
    return os.path.dirname(os.getcwd())


def rev_directory():
    return os.getcwd()


def silentremove(filepath):
    if os.path.exists(filepath):
        if os.path.isfile(filepath) or os.path.islink(filepath):
            os.remove(filepath)  # remove file or symlink
        elif os.path.isdir(filepath):
            shutil.rmtree(filepath)  # remove directory and contents


def path(target_value, structure_dict=None, base_directory=None):

    # returns the filepath/filename of a filekey.
    """
    Recursively searches for a value in a nested JSON structure and returns the path to the element containing that value.

    Args:
        target_value (str): The value to search for.

    Returns:
        list: A list of container names leading to the element containing the target value, or None if not found.
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
        return os.path.join(harnice_root, "library_locations.csv")

    if target_value == "project locations":
        import harnice

        harnice_root = os.path.dirname(
            os.path.dirname(os.path.dirname(harnice.__file__))
        )
        return os.path.join(harnice_root, "project_locations.csv")

    if target_value == "drawnby":
        import harnice

        harnice_root = os.path.dirname(
            os.path.dirname(os.path.dirname(harnice.__file__))
        )
        return os.path.join(harnice_root, "drawnby.json")

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
    """
    Returns the absolute path to a directory identified by its key
    within a dict hierarchy.
    """
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


def verify_revision_structure(product_type=None):
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
    info_row = rev_history.info()
    if info_row in ("row not found", "file not found"):
        rev_history.append(next_rev=state.rev)

    # --- Status must be blank to proceed ---
    if rev_history.info(field="status") != "":
        raise RuntimeError(
            f"Revision {state.rev} status is not clear. "
            f"Harnice only renders revisions with a blank status."
        )

    print(f"Working on PN: {state.pn}, Rev: {state.rev}")
    rev_history.update_datemodified()


def today():
    return datetime.date.today().strftime("%-m/%-d/%y")


def get_git_hash_of_harnice_src():
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
    """
    Given a traceable identifier for a project (PN, URL, etc),
    return the expanded local filesystem path.

    Expects a CSV at the root of the repo named:
        project_locations.csv

    Format (no headers):
        traceable_key,local_path
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
                f"Expected tsv file with delimiter '{delimiter}' at path or key {filepath}"
            )


def drawnby():
    return json.load(open(path("drawnby")))
