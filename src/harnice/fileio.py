import os
import os.path
import json
import time
import subprocess
import shutil
from os.path import basename
from inspect import currentframe
import xml.etree.ElementTree as ET
import re
from dotenv import load_dotenv, dotenv_values
from harnice import(
    rev_history,
    cli
)

pn = ""
rev = 0
#fileio mode:
mode = "unknown"
#valid options:
    #   "partfile" - cwd is in the higher-level part dir
    #   "revisionfile" - cwd is in the lower-level rev dir inside a part dir
    #   "unknown" - structure is not recognized. when verify_revision_structure() is run, this is set to one of the other two
def part_directory():
    if mode == "partfile":
        return os.getcwd()
    elif mode == "revisionfile":
        return os.path.dirname(os.getcwd())
    else:
        raise ValueError(f"Unknown fileio mode: {mode}")
def rev_directory():
    if mode == "partfile":
        return os.path.join(part_directory(), f"{pn}-rev{rev}")
    elif mode == "revisionfile":
        return os.getcwd()
    else:
        raise ValueError(f"Unknown fileio mode: {mode}")

#standard punctuation:
    #  .  separates between name hierarchy levels
    #  _  means nothing, basically a space character
    #  -  if multiple instances are found at the same hierarchy level with the same name, 
                #this separates name from unique instance identifier

def partnumber(format):
    #Returns part numbers in various formats based on the current working directory

    #given a part number "pppppp-revR"

    #format options:
        #pn-rev:    returns "pppppp-revR"
        #pn:        returns "pppppp"
        #rev:       returns "revR"
        #R:         returns "R"

    pn_rev = os.path.basename(rev_directory())

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

    return {
            "editable_component_data":{},
            "support_do_not_edit": {
                "lists":{
                    f"{partnumber("pn-rev")}.harness_bom.tsv":"harness bom",
                    f"{partnumber("pn-rev")}.instances_list.tsv":"instances list",
                    f"{partnumber("pn-rev")}.wirelist.tsv":"wirelist no formats",
                    f"{partnumber("pn-rev")}.wirelist.xls":"wirelist formatted"
                },
                "formboard_data": {
                    f"{partnumber("pn-rev")}.connections_to_graph.json":"connections to graph",
                    f"{partnumber("pn-rev")}.formboard_graph_definition.svg":"formboard graph definition svg"
                },
                "svg_generated": {
                    "tblock_svgs":{},
                    "formboard_svgs":{},
                    f"{partnumber("pn-rev")}.wirelist_master.svg":"wirelist master svg",
                    f"{partnumber("pn-rev")}.revhistory_master.svg":"revhistory master svg",
                    f"{partnumber("pn-rev")}.buildnotes_master.svg":"buildnotes master svg",
                    f"{partnumber("pn-rev")}.bom_table_master.svg":"bom table master svg",
                    f"{partnumber("pn-rev")}.esch_master.svg":"esch master svg",
                    f"{partnumber("pn-rev")}.master.svg":"master svg"
                },
                f"{partnumber("pn-rev")}.flagnotes.json":"flagnotes json"
            },
            "wireviz_outputs":{
                f"{partnumber("pn-rev")}.bom.tsv":"wireviz bom",
                f"{partnumber("pn-rev")}.html":"wireviz html",
                f"{partnumber("pn-rev")}.png":"wireviz png",
                f"{partnumber("pn-rev")}.svg":"wireviz svg"
            },
            "page_setup":{
                f"{partnumber("pn-rev")}.harnice_output_contents.json":"harnice output contents"
            },
            f"{partnumber("pn-rev")}.formboard_graph_definition.json":"formboard graph definition",
            f"{partnumber("pn-rev")}.harnice_output.pdf":"harnice output",
            f"{partnumber("pn-rev")}.buildnotes.tsv":"buildnotes tsv",
            f"{partnumber("pn-rev")}.yaml":"harness yaml",
            f"{partnumber("pn-rev")}.harness_requirements.json":"harness requirements"
        }

def generate_structure():
    #rebuild all from this directory if exists
    if os.path.exists(dirpath("support_do_not_edit")):
        shutil.rmtree(dirpath("support_do_not_edit"))

    os.makedirs(dirpath("editable_component_data"), exist_ok=True)
    os.makedirs(dirpath("support_do_not_edit"), exist_ok=True)
    os.makedirs(dirpath("lists"), exist_ok=True)
    os.makedirs(dirpath("formboard_data"), exist_ok=True)
    os.makedirs(dirpath("svg_generated"), exist_ok=True)
    os.makedirs(dirpath("tblock_svgs"), exist_ok=True)
    os.makedirs(dirpath("formboard_svgs"), exist_ok=True)
    os.makedirs(dirpath("wireviz_outputs"), exist_ok=True)
    os.makedirs(dirpath("page_setup"), exist_ok=True)

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
        file_path = os.path.join(part_directory(), f"{partnumber("pn")}.revision_history.tsv")
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
    return os.path.join(rev_directory(),*path_value)

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
    return os.path.join(rev_directory(),*path_key)

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
    global mode
    global pn
    global rev
    
    cwd_path = os.getcwd()
    cwd_name = os.path.basename(cwd_path)
    parent_dirpath = os.path.dirname(cwd_path)
    parent_dirname = os.path.basename(parent_dirpath)
    children_dir = os.listdir(cwd_path)

    part_path = ""
    rev_path = ""
    pn = ""
    rev = 0
    mode = "unknown"

    mode = getmode()

    # === Mode: Partfile ===
    if any(d.startswith(f"{cwd_name}-rev") for d in children_dir):
        mode = "partfile"
        part_path = cwd_path
        pn = cwd_name
        print(f"You're working on part number: {pn}")

    # === Mode: Revisionfile ===
    elif cwd_name.startswith(f"{parent_dirname}-rev"):
        mode = "revisionfile"
        part_path = parent_dirpath
        rev_path = cwd_path
        pn = parent_dirname
        rev = int(cwd_name.split("-rev")[-1])
        print(f"You're working on part number: {pn}")

    # === Mode: Unknown — Ask user if they want to proceed ===
    if mode == "unknown":
        print("Couldn't identify your file structure. Do you wish to create a new part out of this directory?")
        print(f"Proposed part number: {cwd_name}      Proposed new rev: 1")
        if cli.prompt("Hit y or enter to proceed or any other key to terminate", default='y') == 'y':
            mode = "partfile"
            part_path = cwd_path
            pn = cwd_name
        else:
            exit()
    print(f"!!!{mode}")

    # === Revision History File Handling ===
    revision_history_data = []
    if not os.path.exists(path("revision history")):
        rev_history.generate_revision_history_tsv()

    # === If in Partfile mode, pick a rev ===
    if mode == "partfile":
        highest_rev = 0
        highest_unreleased_rev = None

        print("Revisions in tsv:")
        for revision in revision_history_data:
            r = int(revision.get("rev"))
            if r > highest_rev:
                highest_rev = r
            if revision.get("status", "") == "":
                highest_unreleased_rev = r
            print(f"    {revision.get("rev")}   {revision.get("status")}")
        print()

        if highest_unreleased_rev:
            if cli.prompt(f"Highest unreleased rev is {highest_unreleased_rev}. Hit enter to work on it, otherwise enter desired rev:", default='y') == 'y':
                rev = highest_unreleased_rev
            else:
                rev = int(cli.prompt("Enter desired revision number:"))
        else:
            rev = highest_rev + 1

        rev_path = os.path.join(part_path, f"{pn}-rev{rev}")

    # === If in Revisionfile mode, validate status ===
    elif mode == "revisionfile":
        found = False
        for revision in revision_history_data:
            if str(revision.get("rev", "")) == str(rev):
                found = True
                if revision.get("status", "") != "":
                    raise RuntimeError(f"[ERROR] Status for rev{rev} is not blank. Either unrelease it or `cd ..` and run harnice to create a new rev.")
        if not found:
            raise RuntimeError(f"[ERROR] Revision {rev} not found in {pn}.revisionhistory.tsv. We only add rows automatically if you're in rev1 but since you're not in rev1 please update manually.")

    if rev_history.find_rev_entry_in_tsv(rev) == False:
        if rev == 1:
            message = cli.prompt("Enter a description for this rev", default="Initial release")
        else:
            print("We noticed you're working on a higher rev but it's not recorded in the rev history sheet.")
            message = cli.prompt("    Enter a description for this rev")
        rev_history.append_new_row(rev, message)

    return mode, pn, rev

