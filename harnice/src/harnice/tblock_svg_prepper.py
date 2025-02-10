import json
import re
import os
import shutil
from os.path import basename
from inspect import currentframe
from utility import *

wanted_tblock_libdomain = None
wanted_tblock_libsubpath = None
wanted_tblock_libfilename = None

library_used_tblock_filepath = None

master_svg_dir_filepath = os.path.join(os.getcwd(), "support-do-not-edit", "master-svgs")
tblock_master_svg_filename = f"{partnumber("pn-rev")}-tblock-master.svg"
tblock_master_svg_filepath = os.path.join(master_svg_dir_filepath, tblock_master_svg_filename)

json_tblock_data = None

def pull_tblock_info_from_json():
    # Locate JSON file in `currentdirectory/support-do-not-edit`
    json_file = os.path.join(
        os.getcwd(), "support-do-not-edit", f"{partnumber("pn-rev")}-tblock-master-text.json"
    )
    # Load JSON json_tblock_data
    global json_tblock_data
    with open(json_file, 'r') as jf:
        json_tblock_data = json.load(jf)

    #to-do: pull these from JSON as well
    global wanted_tblock_libdomain
    global wanted_tblock_libsubpath
    global wanted_tblock_libfilename
    wanted_tblock_libdomain = "rs"
    wanted_tblock_libsubpath = "page_defaults"
    wanted_tblock_libfilename = "rs-tblock-default.svg" 

def prep_tblock_svg_master():

    pull_tblock_info_from_json()

    # Ensure the master_svg_dir_filepath exists
    os.makedirs(master_svg_dir_filepath, exist_ok=True)

    global library_used_tblock_filepath
    library_used_tblock_filepath = os.path.join(os.getcwd(), "library_used", wanted_tblock_libsubpath, wanted_tblock_libfilename)

    # Grab the latest format from the library
    import_file_from_harnice_library(wanted_tblock_libdomain, wanted_tblock_libsubpath, wanted_tblock_libfilename)

    #delete existing master svg to refresh it from library-used
    if os.path.exists(tblock_master_svg_filepath):
        os.remove(tblock_master_svg_filepath)
        
    #move it to the svg master folder
    shutil.copy(library_used_tblock_filepath, master_svg_dir_filepath)

    #rename it to match the convention
    os.rename(os.path.join(master_svg_dir_filepath, wanted_tblock_libfilename), tblock_master_svg_filepath)
    
    # Find info to populate into title block from the json file...

    # Read input file content
    with open(tblock_master_svg_filepath, 'r') as inf:
        content = inf.read()

    # Replace each occurrence of "unique-id-<jsonfilefield>"
    pattern = r"tblock-key-(\w+)"
    def replacer(match):
        key = match.group(1)  # Extract the field name
        old_text = match.group(0)  # The full placeholder text
        new_text = str(json_tblock_data.get(key, old_text))  # Get replacement text or keep original
        print(f"Replacing: '{old_text}' with: '{new_text}'")  # Print the replacement info
        return new_text

    updated_content = re.sub(pattern, replacer, content)

    # Overwrite the input file with the updated content
    with open(tblock_master_svg_filepath, 'w') as inf:
        inf.write(updated_content)
        print("Updated tblock info.")

    


if __name__ == "__main__":
    prep_tblock_svg_master()