import os
import os.path
import json
import datetime
import subprocess
import shutil
from os.path import basename
from inspect import currentframe
import xml.etree.ElementTree as ET
import re
import csv
from dotenv import load_dotenv, dotenv_values
from harnice import(
    rev_history,
    cli,
    component_library
)

#standard punctuation:
    #  .  separates between name hierarchy levels
    #  _  means nothing, basically a space character
    #  -  if multiple instances are found at the same hierarchy level with the same name, 
                #this separates name from unique instance identifier

product_type = ""

pn = ""
rev = 0
#fileio mode:
mode = "unknown"
#valid options:
    #   "partfile" - cwd is in the higher-level part dir
    #   "revisionfile" - cwd is in the lower-level rev dir inside a part dir
    #   "unknown" - structure is not recognized. when verify_revision_structure() is run, this is set to one of the other two

def _part_directory():
    return os.path.dirname(os.getcwd())

def _rev_directory():
    return os.getcwd()

def set_product_type(x):
    global product_type
    product_type = x

def partnumber(format):
    #Returns part numbers in various formats based on the current working directory

    #given a part number "pppppp-revR"

    #format options:
        #pn-rev:    returns "pppppp-revR"
        #pn:        returns "pppppp"
        #rev:       returns "revR"
        #R:         returns "R"

    pn_rev = os.path.basename(_rev_directory())

    if format == "pn-rev":
        return pn_rev

    elif format == "pn":
        match = re.search(r"-rev", pn_rev)
        if match:
            return pn_rev[:match.start()]

    elif format == "rev":
        match = re.search(r"-rev", pn_rev)
        if match:
            return pn_rev[match.start() + 1:]

    elif format == "R":
        match = re.search(r"-rev", pn_rev)
        if match:
            return pn_rev[match.start() + 4:]

    else:
        raise ValueError("Function 'partnumber' not presented with a valid format")

def harnice_file_structure():
    #syntax:
    #   "filename": "filekey"

    #filename is the actual file name with a suffix
    #filekey is the shorthand reference for it with no suffix

    if product_type == "harness":
        return {
                f"{partnumber("pn-rev")}-feature_tree.py":"feature tree",
                f"{partnumber("pn-rev")}-instances_list.tsv":"instances list",
                "artifacts":{
                    f"{partnumber("pn-rev")}-formboard_graph_definition.svg":"formboard graph definition svg",
                },
                "instance_data":{
                    "imported_instances":{},
                    "generated_instances_do_not_edit":{}
                },
                "interactive_files":{
                    f"{partnumber("pn-rev")}.formboard_graph_definition.tsv":"formboard graph definition",
                    f"{partnumber("pn-rev")}.flagnotes.tsv":"flagnotes manual"
                },
                "prebuilders":{}
            }
    elif product_type == "part":
        return {
            f"{partnumber("pn-rev")}-drawing.svg":"drawing",
            f"{partnumber("pn-rev")}-attributes.json":"attributes"
        }
    elif product_type == "flagnote":
        return {
            f"{partnumber("pn-rev")}-params.json":"params",
            f"{partnumber("pn-rev")}-drawing.svg":"drawing",
        }
    elif product_type in ("tblock", "titleblock"):
        return {
            f"{partnumber("pn-rev")}-params.json":"params",
            f"{partnumber("pn-rev")}-drawing.svg":"drawing",
            f"{partnumber("pn-rev")}-attributes.json":"attributes"
        }
    elif product_type == "device":
        return {
            f"{partnumber("pn-rev")}.kicad_sym":"kicad sym",
            f"{partnumber("pn-rev")}-feature_tree.py":"feature tree",
            f"{partnumber("pn-rev")}-signals-list.tsv":"signals list"
        }
    elif product_type == "system":
        return {
            f"{partnumber("pn-rev")}-feature_tree.py":"feature tree",
            f"{partnumber("pn-rev")}-netlist.json":"netlist",
            f"{partnumber("pn-rev")}-chmap.tsv":"channel map",
            f"{partnumber("pn-rev")}-bom.tsv":"bom",
            f"{partnumber("pn-rev")}-instances_list.tsv":"instances list",
            "mapped_channels.txt":"mapped channels set",
            "prebuilders":{},
            "imported_devices":{}
        }

def generate_structure():
    os.makedirs(dirpath("artifacts"), exist_ok=True)
    os.makedirs(dirpath("instance_data"), exist_ok=True)
    os.makedirs(dirpath("imported_instances"), exist_ok=True)
    silentremove(dirpath("generated_instances_do_not_edit"))
    os.makedirs(dirpath("generated_instances_do_not_edit"), exist_ok=True)
    os.makedirs(dirpath("interactive_files"), exist_ok=True)
    os.makedirs(dirpath("prebuilders"), exist_ok=True)

def silentremove(filepath):
    if os.path.exists(filepath):
        if os.path.isfile(filepath) or os.path.islink(filepath):
            os.remove(filepath)  # remove file or symlink
        elif os.path.isdir(filepath):
            shutil.rmtree(filepath)  # remove directory and contents

def path(target_value):
    #returns the filepath/filename of a filekey. 
    """
    Recursively searches for a value in a nested JSON structure and returns the path to the element containing that value.

    Args:
        target_value (str): The value to search for.

    Returns:
        list: A list of container names leading to the element containing the target value, or None if not found.
    """
    if target_value == "revision history":
        file_path = os.path.join(_part_directory(), f"{partnumber("pn")}-revision_history.tsv")
        return file_path

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

    path_value = recursive_search(harnice_file_structure(), [])
    if not path_value:
        raise TypeError(f"Could not find filepath of {target_value}.")
    return os.path.join(_rev_directory(),*path_value)

def dirpath(target_key):
    #returns the path of a directory you know the name of. use that directory name as the argument. 

    def recursive_search(data, path):
        if isinstance(data, dict):
            for key, value in data.items():
                if key == target_key:
                    return path + [key]
                result = recursive_search(value, path + [key])
                if result:
                    return result
        elif isinstance(data, list):
            for index, item in enumerate(data):
                result = recursive_search(item, path + [f"[{index}]"])
                if result:
                    return result
        return None

    path_key = recursive_search(harnice_file_structure(), [])
    if not path_key:
        raise TypeError(f"Could not find directory {target_key}.")
    return os.path.join(_rev_directory(),*path_key)

def name(target_value):
    #returns the filename of a filekey. 
    """
    Recursively searches for a value in a nested JSON structure and returns the key containing that value.

    Args:
        target_value (str): The value to search for.

    Returns:
        str: The key containing the target value, or None if not found.
    """

    def recursive_search(data):
        if isinstance(data, dict):
            for key, value in data.items():
                if value == target_value:
                    return key
                result = recursive_search(value)
                if result:
                    return result
        elif isinstance(data, list):
            for item in data:
                result = recursive_search(item)
                if result:
                    return result
        return None

    if not recursive_search(harnice_file_structure()):
        raise TypeError(f"Could not find filename of key {target_value}.")

    return recursive_search(harnice_file_structure())

def verify_revision_structure():
    cwd = os.getcwd()
    cwd_name = os.path.basename(cwd)
    parent = os.path.basename(os.path.dirname(cwd))
    temp_tsv_path = os.path.join(os.getcwd(), f"{cwd_name}-revision_history.tsv")

    def is_revision_folder(name, parent_name):
        return name.startswith(f"{parent_name}-rev") and name.split("-rev")[-1].isdigit()

    def has_revision_folder_inside(path, pn):
        pattern = re.compile(rf"{re.escape(pn)}-rev\d+")
        return any(pattern.fullmatch(d) for d in os.listdir(path))

    def make_new_rev_tsv(path, pn, rev):
        columns = rev_history.revision_history_columns()
        
        # Ensure file exists with header
        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=columns, delimiter='\t')
            writer.writeheader()
        append_row_to_tsv(path, pn, rev)

    def append_row_to_tsv(path, pn, rev):
        if not os.path.exists(path):
            return "file not found"

        with open(path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='\t')
            rows = list(csv.DictReader(f, delimiter='\t'))
            fieldnames = reader.fieldnames

        # Build the row with required fields and blank others
        desc = rev_history.initial_release_desc()
        if not desc:
            desc = "HARNESS, DOES A, FOR B"
        desc = cli.prompt("Enter a description of this part", default=desc)

        revisionupdates = "INITIAL RELEASE"
        if rev_history.initial_release_exists():
            revisionupdates = ""
        revisionupdates = cli.prompt("Enter a description for this revision", default=revisionupdates)
        while not revisionupdates or not revisionupdates.strip():
                print("Revision updates can't be blank!")
                revisionupdates = cli.prompt("Enter a description for this revision", default=None)

        rows.append({
            "pn": pn,
            "rev": rev,
            "desc": desc,
            "rev": rev,
            "status": "",
            "datestarted": today(),
            "datemodified": today(),
            "revisionupdates": revisionupdates
        })

        # Append the row
        columns = rev_history.revision_history_columns()
        with open(path, "w", newline='') as f:
            writer = csv.DictWriter(f, fieldnames=columns, delimiter='\t')
            writer.writeheader()
            writer.writerows(rows)

    def prompt_new_part(part_dir, pn):
        rev = cli.prompt("Enter revision number", default="1")
        # append to TSV
        make_new_rev_tsv(temp_tsv_path, pn, rev)
        # create and cd into rev folder
        folder = os.path.join(part_dir, f"{pn}-rev{rev}")
        os.makedirs(folder, exist_ok=True)
        os.chdir(folder)
        return rev

    # 1) Already in a <PN>-revN folder?
    if is_revision_folder(cwd_name, parent):
        pn = parent
        rev = int(cwd_name.split("-rev")[-1])

    # 2) In a part folder (has rev folders inside)?
    elif has_revision_folder_inside(cwd, cwd_name):
        print(f"This is a part folder ({cwd_name}).")
        print(f"Please `cd` into one of its revision subfolders (e.g. `{cwd_name}-rev1`) and rerun.")
        exit()

    # 3) Unknown – offer to initialize a new PN here
    else:
        answer = cli.prompt(f"No revision structure detected in '{cwd_name}'. Create new PN here?", default="y")
        if answer.lower() not in ("y", "yes", ""):
            exit()
        pn = cwd_name
        rev = prompt_new_part(cwd, pn)

    # if everything looks good but the tsv isn't
    x = rev_history.revision_info()
    if x == "row not found":
        append_row_to_tsv(path("revision history"), pn, rev)
    elif x == "file not found":
        make_new_rev_tsv(path("revision history"), pn, rev)

     # — now we’re in a revision folder, with pn, rev, temp_tsv_path set —
    if not rev_history.status(rev) == "":
        raise RuntimeError(f"Revision {rev} status is not clear. Harnice will only let you render revs with a blank status.")


    print(f"Working on PN: {pn}, Rev: {rev}")
    return pn, rev

def today():
    return datetime.date.today().strftime("%-m/%-d/%y")
