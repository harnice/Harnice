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
        raise ValueError("Function 'file.partnumber' not presented with a valid format")

#TODO: rename_file(old_name, new_name, print_report) should be changed to os.rename(old_name, new_name)

#TODO: file_exists_in_directory(search_for_filename, directory=".") should be changed to os.path.isfile(os.path.join(directory, search_for_filename))

def harnice_file_structure():
    return {
            "drawing_instances":{},
            "library_used":{},
            "support_do_not_edit": {
                "boms":{
                    f"{file.partnumber("pn-rev")}.esch_electrical_bom.tsv":"electrical bom",
                    f"{file.partnumber("pn-rev")}.harness_bom.tsv":"harness bom",
                    f"{file.partnumber("pn-rev")}.mechanical_bom.tsv":"mechanical bom",
                    f"{file.partnumber("pn-rev")}.instances_list.tsv":"instances list"
                },
                "formboard_data": {
                    f"{file.partnumber("pn-rev")}.connections_to_graph.json":"connections to graph",
                    f"{file.partnumber("pn-rev")}.formboard_node_locations_inches.json":"formboard node locations inches",
                    f"{file.partnumber("pn-rev")}.formboard_node_locations_px.json":"formboard node locations px",
                    f"{file.partnumber("pn-rev")}.formboard_segment_to_from_center.json":"formboard segment to from center",
                    f"{file.partnumber("pn-rev")}.formboard_graph_definition.svg":"formboard graph definition svg"
                },
                "master_svgs": {
                    f"{file.partnumber("pn-rev")}.bom_table_master.svg":"bom table master svg",
                    f"{file.partnumber("pn-rev")}.esch_master.svg":"esch master svg",
                    f"{file.partnumber("pn-rev")}.formboard_master.svg":"formboard master svg",
                    f"{file.partnumber("pn-rev")}.tblock_master.svg":"tblock master svg",
                    f"{file.partnumber("pn-rev")}.revhistory_master.svg":"revhistory master svg",
                    f"{file.partnumber("pn-rev")}.buildnotes_master.svg":"buildnotes master svg"
                },
                "wirelists": {
                    f"{file.partnumber("pn-rev")}.wirelist_nolengths.tsv":"wirelist nolengths",
                    f"{file.partnumber("pn-rev")}.wirelist_lengths.tsv":"wirelist lengths"
                },
                f"{file.partnumber("pn-rev")}.tblock_master_text.json":"tblock master text",
                f"{file.partnumber("pn-rev")}.flagnote_instance_matrix.tsv":"flagnote instance matrix"
            },
            "wireviz_outputs":{
                f"{file.partnumber("pn-rev")}.bom.tsv":"wireviz bom",
                f"{file.partnumber("pn-rev")}.html":"wireviz html",
                f"{file.partnumber("pn-rev")}.png":"wireviz png",
                f"{file.partnumber("pn-rev")}.svg":"wireviz svg"
            },
            f"{file.partnumber("pn-rev")}.formboard_graph_definition.json":"formboard graph definition",
            f"{file.partnumber("pn-rev")}.harnice_output.svg":"harnice output",
            f"{file.partnumber("pn-rev")}.buildnotes.tsv":"buildnotes tsv",
            f"{file.partnumber("pn-rev")}.yaml":"harness yaml"
        }

def generate_structure():
    os.makedirs(file.dirpath("drawing_instances"), exist_ok=True)
    os.makedirs(file.dirpath("library_used"), exist_ok=True)
    os.makedirs(file.dirpath("support_do_not_edit"), exist_ok=True)
    os.makedirs(file.dirpath("boms"), exist_ok=True)
    os.makedirs(file.dirpath("formboard_data"), exist_ok=True)
    os.makedirs(file.dirpath("master_svgs"), exist_ok=True)
    os.makedirs(file.dirpath("wirelists"), exist_ok=True)
    os.makedirs(file.dirpath("wireviz_outputs"), exist_ok=True)

def path(target_value):
    #returns the filepath/filename of a filekey. 
    """
    Recursively searches for a value in a nested JSON structure and returns the path to the element containing that value.

    Args:
        target_value (str): The value to search for.

    Returns:
        list: A list of container names leading to the element containing the target value, or None if not found.
    """

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