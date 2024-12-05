import json
import re
import os
from os.path import basename
from inspect import currentframe
from utility import pn_from_dir, import_file_from_harnice_library, copy_file_to_directory, delete_file, rename_file
from harnice_paths import harnice_library_path

def prep_tblock_svg_master():
    # Grab the latest format from the library
    import_file_from_harnice_library("rs", "page_defaults", "rs-tblock-default.svg")
    
    input_file = f"{pn_from_dir()}-tblock-master.svg"
    master_svgs_dir = os.path.join(os.getcwd(), "support-do-not-edit", "master-svgs")
    
    # Ensure the master_svgs_dir exists
    os.makedirs(master_svgs_dir, exist_ok=True)

    # Delete the existing instance in master_svgs_dir if it exists
    existing_file_path = os.path.join(master_svgs_dir, input_file)
    if os.path.exists(existing_file_path):
        delete_file(existing_file_path)
    
    # Copy default SVG to current directory
    copy_file_to_directory(
        os.path.join(os.getcwd(), "library_used/page_defaults/rs-tblock-default.svg"), 
        os.getcwd()
    )

    # Rename the file
    rename_file("rs-tblock-default.svg", input_file, False)
    
    # Move the renamed file to the master_svgs_dir
    os.rename(input_file, existing_file_path)

    # Locate JSON file in `currentdirectory/support-do-not-edit`
    json_file = os.path.join(
        os.getcwd(), "support-do-not-edit", f"{pn_from_dir()}-tblock-master-text.json"
    )

    # Replace unique IDs in the input SVG file
    replace_unique_ids(json_file, existing_file_path)

def replace_unique_ids(json_file, input_file):
    # Load JSON data
    with open(json_file, 'r') as jf:
        data = json.load(jf)

    # Read input file content
    with open(input_file, 'r') as inf:
        content = inf.read()

    # Replace each occurrence of "unique-id-<jsonfilefield>"
    pattern = r"unique-key-(\w+)"
    def replacer(match):
        key = match.group(1)  # Extract the field name
        return str(data.get(key, match.group(0)))  # Replace or keep original if not found

    updated_content = re.sub(pattern, replacer, content)

    # Overwrite the input file with the updated content
    with open(input_file, 'w') as inf:
        inf.write(updated_content)

    print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Replacements complete. {input_file} has been updated.")


if __name__ == "__main__":
    prep_tblock_svg_master()
