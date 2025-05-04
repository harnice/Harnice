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


#standard punctuation:
    #  .  separates between name hierarchy levels
    #  _  means nothing, basically a space character
    #  -  if multiple instances are found at the same hierarchy level with the same name, this separates name from unique instance identifier

#here's the ultimate definition of all Harnice project files:

#syntax:
#"filename": "filekey"

#filename is the actual file name with a suffix
#filekey is the shorthand reference for it with no suffix

def partnumber(format):
    #Returns part numbers in various formats based on the current working directory

    #given a part number "pppppp-revR"

    #format options:
        #pn-rev:    returns "pppppp-revR"
        #pn:        returns "pppppp"
        #rev:       returns "revR"
        #R:         returns "R"

    pn_rev = os.path.basename(os.getcwd())

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
                "master_svgs": {
                    f"{partnumber("pn-rev")}.bom_table_master.svg":"bom table master svg",
                    f"{partnumber("pn-rev")}.esch_master.svg":"esch master svg",
                    f"{partnumber("pn-rev")}.formboard_master.svg":"formboard master svg",
                    f"{partnumber("pn-rev")}.tblock_master.svg":"tblock master svg",
                    f"{partnumber("pn-rev")}.revhistory_master.svg":"revhistory master svg",
                    f"{partnumber("pn-rev")}.buildnotes_master.svg":"buildnotes master svg"
                },
                f"{partnumber("pn-rev")}.flagnote_instance_matrix.tsv":"flagnote instance matrix"
            },
            "wireviz_outputs":{
                f"{partnumber("pn-rev")}.bom.tsv":"wireviz bom",
                f"{partnumber("pn-rev")}.html":"wireviz html",
                f"{partnumber("pn-rev")}.png":"wireviz png",
                f"{partnumber("pn-rev")}.svg":"wireviz svg"
            },
            "page_setup":{
                f"{partnumber("pn-rev")}.titleblock_setup.json":"titleblock setup",
                f"{partnumber("pn-rev")}.formboard_scale.json":"formboard scale"
            },
            f"{partnumber("pn-rev")}.formboard_graph_definition.json":"formboard graph definition",
            f"{partnumber("pn-rev")}.harnice_output.svg":"harnice output",
            f"{partnumber("pn-rev")}.buildnotes.tsv":"buildnotes tsv",
            f"{partnumber("pn-rev")}.yaml":"harness yaml",
            f"{partnumber("pn-rev")}.harness_requirements.json":"harness requirements"
        }

def generate_structure():
    os.makedirs(dirpath("editable_component_data"), exist_ok=True)
    os.makedirs(dirpath("support_do_not_edit"), exist_ok=True)
    os.makedirs(dirpath("lists"), exist_ok=True)
    os.makedirs(dirpath("formboard_data"), exist_ok=True)
    os.makedirs(dirpath("master_svgs"), exist_ok=True)
    os.makedirs(dirpath("wireviz_outputs"), exist_ok=True)

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
        file_path = os.path.join(os.path.dirname(os.getcwd()), f"{partnumber("pn")}-revision_history.tsv")
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
    return os.path.join(os.getcwd(),*path_value)

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
    return os.path.join(os.getcwd(),*path_key)

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

