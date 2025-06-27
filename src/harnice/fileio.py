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
    cli
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

    def make_new_rev_tsv(pn, rev):
        columns = rev_history.revision_history_columns()
        
        # Ensure file exists with header
        if not os.path.exists(temp_tsv_path):
            with open(temp_tsv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=columns, delimiter='\t')
                writer.writeheader()

        append_row_to_tsv(temp_tsv_path, pn, rev)

    def append_row_to_tsv(path, pn, rev):
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

        today = datetime.date.today().isoformat()

        rows.append({
            "pn": pn,
            "rev": rev,
            "desc": desc,
            "rev": rev,
            "status": "",
            "datestarted": today,
            "datemodified": today,
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
        make_new_rev_tsv(pn, rev)
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

    # if everything looks good but the row isn't in the tsv file
    try:
        rev_history.revision_info()
    except:
        print("Couldn't find this rev in the revision history TSV. Please add some info first...")
        append_row_to_tsv(path("revision history"), pn, rev)

     # — now we’re in a revision folder, with pn, rev, temp_tsv_path set —
    if not rev_history.status(rev) == "":
        raise RuntimeError(f"Revision {rev} status is not clear. Harnice will only let you render revs with a blank status.")


    print(f"Working on PN: {pn}, Rev: {rev}")
    return pn, rev

def verify_yaml_exists():
    if not os.path.exists(path("harness yaml")):
        print()
        print("    No YAML harness definition file found.")
        print()
        exit()