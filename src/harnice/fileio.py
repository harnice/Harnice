import os
import os.path
import datetime
import shutil
import re
import csv

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


def path(target_value, structure_dict=None):
    if structure_dict is None:
        structure_dict = file_structure()

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
            part_directory(), f"{partnumber('pn')}-revision_history.tsv"
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

    # FILES INSIDE OF A STRUCURE DEFINED BY FILEIO
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
    return os.path.join(rev_directory(), *path_value)


def dirpath(target_key, structure_dict=None):
    if structure_dict is None:
        structure_dict = file_structure()
    """
    Returns the absolute path to a directory identified by its key
    within a dict hierarchy.
    """

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
    # join all levels to construct a valid path
    return os.path.join(rev_directory(), *path_key)


def verify_revision_structure(product_type=None):
    from harnice.lists import rev_history
    from harnice import cli

    cwd = os.getcwd()
    cwd_name = os.path.basename(cwd)
    parent = os.path.basename(os.path.dirname(cwd))
    temp_tsv_path = os.path.join(os.getcwd(), f"{cwd_name}-revision_history.tsv")

    def is_revision_folder(name, parent_name):
        return (
            name.startswith(f"{parent_name}-rev") and name.split("-rev")[-1].isdigit()
        )

    def has_revision_folder_inside(path, pn):
        pattern = re.compile(rf"{re.escape(pn)}-rev\d+")
        return any(pattern.fullmatch(d) for d in os.listdir(path))

    def prompt_new_part(part_dir, pn):
        rev = int(cli.prompt("Enter revision number", default="1"))
        rev_history.new(temp_tsv_path, pn, rev)
        folder = os.path.join(part_dir, f"{pn}-rev{rev}")
        os.makedirs(folder, exist_ok=True)
        os.chdir(folder)
        return rev

    # 1) Already in a <PN>-revN folder?
    if is_revision_folder(cwd_name, parent):
        pn = parent
        rev = int(cwd_name.split("-rev")[-1])  # already in a rev folder

    # 2) In a part folder (has rev folders inside)?
    elif has_revision_folder_inside(cwd, cwd_name):
        print(f"This is a part folder ({cwd_name}).")
        print(
            f"Please `cd` into one of its revision subfolders (e.g. `{cwd_name}-rev1`) and rerun."
        )
        exit()  # cancels if not in a rev folder

    # 3) Unknown – offer to initialize a new PN here
    else:
        answer = cli.prompt(
            f"No revision structure detected in '{cwd_name}'. Create new PN here?",
            default="y",
        )
        if answer.lower() not in ("y", "yes", ""):
            exit()
        pn = cwd_name
        rev = prompt_new_part(cwd, pn)  # changes the cwd to the new rev folder

    # if everything looks good but the tsv isn't there
    x = rev_history.info()
    if x == "row not found":
        append_revision_row(path("revision history"), pn, rev)
    elif x == "file not found":
        make_new_rev_tsv(path("revision history"), pn, rev)

    # now we’re in a revision folder, with pn, rev, temp_tsv_path set
    if not rev_history.info(field="status") == "":
        raise RuntimeError(
            f"Revision {rev} status is not clear. Harnice will only let you render revs with a blank status."
        )

    print(f"Working on PN: {pn}, Rev: {rev}")
    rev_history.update_datemodified()

    return pn, rev


def today():
    return datetime.date.today().strftime("%-m/%-d/%y")


def get_path_to_project(traceable_key):
    # takes in a project repo traceable key and returns the expanded local path
    # traceable key is some unique identifier for this project (project part number, github url, etc)

    for project in read_tsv("project locations", delimiter=","):
        if project.get("traceable_key").strip() == traceable_key.strip():
            local_path = project.get("local_path")
            if not local_path:
                raise ValueError(f"No project local path found for {traceable_key}")
            return os.path.expanduser(local_path)

    raise ValueError(f"Could not find library repo id {traceable_key}")


def read_tsv(filepath, delimiter="\t"):
    if not os.path.exists(filepath):
        raise FileNotFoundError(
            f"Expected tsv file with delimiter '{delimiter}' at: {filepath}"
        )
    with open(filepath, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter=delimiter))