import json
import re
import os
import shutil
from os.path import basename
from inspect import currentframe

import file

wanted_tblock_libdomain = None
wanted_tblock_libsubpath = None
wanted_tblock_libfilename = None

library_used_tblock_filepath = None
json_tblock_data = None

def pull_tblock_info_from_json():
    # Load JSON json_tblock_data
    global json_tblock_data
    with open(file.path("tblock master text"), 'r') as jf:
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

    global library_used_tblock_filepath
    library_used_tblock_filepath = os.path.join(os.getcwd(), "library_used", wanted_tblock_libsubpath, wanted_tblock_libfilename)

    # Grab the latest format from the library
    import_file_from_harnice_library(wanted_tblock_libdomain, wanted_tblock_libsubpath, wanted_tblock_libfilename)

    #delete existing master svg to refresh it from library-used
    if os.path.exists(file.path("tblock master svg")):
        os.remove(file.path("tblock master svg"))
        
    #move it to the svg master folder
    shutil.copy(library_used_tblock_filepath, dirpath("master_svgs"))

    #rename it to match the convention
    os.rename(os.path.join(dirpath("master_svgs"), wanted_tblock_libfilename), file.path("tblock master svg"))
    
    # Find info to populate into title block from the json file...

    # Read input file content
    with open(file.path("tblock master svg"), 'r') as inf:
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
    with open(file.path("tblock master svg"), 'w') as inf:
        inf.write(updated_content)
        print("Updated tblock info.")

    


if __name__ == "__main__":
    prep_tblock_svg_master()