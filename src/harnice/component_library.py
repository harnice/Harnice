import xml.etree.ElementTree as ET
import math
import xml.dom.minidom
import os
import csv
import json
import re
from dotenv import load_dotenv, dotenv_values
from os.path import basename
from inspect import currentframe
import shutil
import filecmp
from harnice import(
    fileio,
    harnice_prechecker,
    instances_list,
    instances_list
)

def pull_parts():
    load_dotenv()
    global drawing_instance_filenames
    supported_library_components = ['connector', 'backshell']
    instances = instances_list.read_instance_rows()

    updated_instances = []
    print()

    for instance in instances:
        #if the type of instance is supported by harnice library
        if instance.get('item_type', '').lower() in supported_library_components:
            
            #find the highest rev in the library
            highest_rev = ""  # default
            try:
                with open(
                    os.path.join(
                        os.getenv(instance.get('supplier')),
                        "parts",
                        instance.get('mpn', ''),
                        f"{instance.get('mpn', '')}-revision_history.tsv"
                    ),
                    newline='', encoding='utf-8'
                ) as f:
                    reader = csv.DictReader(f, delimiter='\t')
                    for rev_entry in reader:
                        rev_str = rev_entry.get('rev', '').strip()
                        if rev_str.isdigit():
                            rev_num = int(rev_str)
                            if highest_rev == "" or rev_num > int(highest_rev):
                                highest_rev = str(rev_num)
            except FileNotFoundError:
                print(f"Missing revision history document. Update your library and rerun.")

            #see if that library instance has already been imported
            exists_bool, exists_rev = exists_in_lib_used(instance.get('instance_name'), instance.get('mpn'))
            instance['lib_rev_used_here'] = exists_rev

            #find latest release in library
            instance['lib_latest_rev'] = highest_rev

            # build paths
            mpn = instance.get('mpn')
            mpn_rev = f"{mpn}-rev{highest_rev}"
            source_lib_path = os.path.join(os.getenv(instance.get('supplier')), "parts", mpn, mpn_rev)
            target_directory = os.path.join(fileio.dirpath("editable_component_data"), instance.get('instance_name'), "library_used_do_not_edit", mpn_rev)

            # Check for outdated or modified libs
            latest = instance.get('lib_latest_rev')
            used = instance.get('lib_rev_used_here')

            if not exists_bool:
                shutil.copytree(source_lib_path, target_directory)
                used = latest

            if int(latest) > int(used):
                print(f"There's a newer revision available for {instance.get("instance_name")}. If you want to update, delete 'support_do_not_edit' within the instance directory.")
            elif int(latest) < int(used):
                print(f"Somehow you've imported a revision of {instance.get("instance_name")} that's newer than what's in the library. You goin crazy!")
                exit()
            else:
                if find_modifications(source_lib_path, target_directory) == False:
                    print(f"Library for '{instance.get("instance_name")}' is up to date.")
                else:
                    raise RuntimeError(
                        f"Either you've modified the {instance.get("instance_name")} library as-imported (not allowed for traceability purposes) or the library has changed without adding a new rev. Either choose a different rev or delete the libraries used from the part to re-import."
                    )

            #COPY IN EDITABLE FILE
            # Patterns to match → new filename template (case-sensitive)
            patterns = [
                (re.compile(r'.*-attributes\.json$'), f"{instance.get('instance_name')}-attributes.json"),
                (re.compile(r'.*-drawing\.svg$'), f"{instance.get('instance_name')}-drawing.svg"),
            ]

            """
            For a given instance_name, copies editable files from:
            drawing_instances/<instance_name>/library_used_do_not_edit/<mpn-rev>/
            to:
            drawing_instances/<instance_name>/

            Files copied:
            *-attributes.json → <instance_name>-attributes.json
            *-drawing.svg     → <instance_name>-drawing.svg

            Only copies if the destination file does not already exist.

            Returns:
                A list of dicts: [{source_filename: ..., destination_filename: ...}, ...]
            """
            copied_files = []

            base_dir = fileio.dirpath("editable_component_data")
            src_root = os.path.join(base_dir, instance.get('instance_name'), "library_used_do_not_edit")
            dst_dir = os.path.join(base_dir, instance.get('instance_name'))

            # Validate exactly one subfolder (mpn-rev)
            try:
                subfolders = [name for name in os.listdir(src_root)
                            if os.path.isdir(os.path.join(src_root, name))]
            except FileNotFoundError:
                return copied_files  # library_used_do_not_edit does not exist

            if len(subfolders) != 1:
                raise RuntimeError(f"Expected exactly one mpn-rev folder in {src_root}, found: {subfolders}")

            mpn_rev_folder = subfolders[0]
            src_dir = os.path.join(src_root, mpn_rev_folder)

            for filename in os.listdir(src_dir):
                src_file = os.path.join(src_dir, filename)

                if not os.path.isfile(src_file):
                    continue

                for pattern, dest_name in patterns:
                    if pattern.match(filename):
                        dst_file = os.path.join(dst_dir, dest_name)
                        if not os.path.exists(dst_file):
                            shutil.copy2(src_file, dst_file)
                            copied_files.append({
                                "source_filename": src_file,
                                "destination_filename": dst_file
                            })
                            
                            #FIND AND REPLACE CONTENTS GROUP WITH INSTANCE NAME GROUPS
                            with open(dst_file, 'r', encoding='utf-8') as file:
                                content = file.read()

                            content = content.replace(f"{instance.get("mpn")}-contents-start", f"{instance.get("instance_name")}-contents-start")
                            content = content.replace(f"{instance.get("mpn")}-contents-end", f"{instance.get("instance_name")}-contents-end")

                            with open(dst_file, 'w', encoding='utf-8') as file:
                                file.write(content)
                        break


        else:
            print(f"Library for '{instance.get('instance_name')}' with component type '{instance.get('item_type')}' either not needed or not supported")

        updated_instances.append(instance)

    # Write all modified rows back at once
    fieldnames = updated_instances[0].keys()
    with open(fileio.path("instances list"), "w", newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter='\t')
        writer.writeheader()
        writer.writerows(updated_instances)  

def exists_in_lib_used(instance_name, mpn):
    # Look for revision folders inside library_used/<instance_name>/
    base_path = os.path.join(fileio.dirpath("editable_component_data"), instance_name, "library_used_do_not_edit")

    try:
        for name in os.listdir(base_path):
            full_path = os.path.join(base_path, name)
            if os.path.isdir(full_path) and name.startswith(mpn):
                match = re.search(r'rev(\d+)', name, re.IGNORECASE)
                if match:
                    return True, match.group(1)
    except FileNotFoundError:
        return False, ""

    return False, ""

def find_modifications(dir1, dir2):
    # Perform a recursive comparison
    dir_comparison = filecmp.dircmp(dir1, dir2)

    # Check for any differences in files or subdirectories
    if dir_comparison.left_only or dir_comparison.right_only or dir_comparison.funny_files:
        return True

    (match, mismatch, errors) = filecmp.cmpfiles(
        dir1, dir2, dir_comparison.common_files, shallow=False
    )
    if mismatch or errors:
        return True

    # Recursively check subdirectories
    for subdir in dir_comparison.common_dirs:
        subdir1 = os.path.join(dir1, subdir)
        subdir2 = os.path.join(dir2, subdir)
        if detect_modified_files(subdir1, subdir2):
            return True

    return False