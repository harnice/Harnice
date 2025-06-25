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
    rev_history,
    instances_list,
    instances_list
)

def pull_item_from_library(supplier, lib_subpath, mpn, desired_rev, destination_directory, used_rev=None, item_name=None):
    if item_name == "":
        item_name = mpn

    base_path = os.path.join(os.getenv(supplier), lib_subpath, mpn)
    rev_file = os.path.join(base_path, f"{mpn}.revision_history.tsv")

    # === Find latest revision from library ===
    latest_rev = ""
    try:
        with open(rev_file, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='\t')
            for row in reader:
                rev_str = row.get('rev', '').strip()
                if rev_str.isdigit():
                    rev_num = int(rev_str)
                    if latest_rev == "" or rev_num > int(latest_rev):
                        latest_rev = str(rev_num)
    except FileNotFoundError:
        print(f"{item_name:<24}  revision history missing")
        return None

    # === Handle "latest" rev logic ===
    if desired_rev == "latest":
        existing_revs = []
        lib_used_path = os.path.join(destination_directory, "library_used_do_not_edit")
        if os.path.exists(lib_used_path):
            for name in os.listdir(lib_used_path):
                match = re.search(rf'{re.escape(mpn)}-rev(\d+)$', name)
                if match:
                    existing_revs.append(int(match.group(1)))

        if existing_revs:
            rev_to_use = str(max(existing_revs))
            source_lib_path = os.path.join(base_path, f"{mpn}-rev{rev_to_use}")
            target_lib_path = os.path.join(destination_directory, "library_used_do_not_edit", f"{mpn}-rev{rev_to_use}")

            if not find_modifications(source_lib_path, target_lib_path):
                print(f"{item_name:<24}  up to date with existing rev (rev{rev_to_use})")
            else:
                raise RuntimeError(f"{item_name}: local copy of rev {rev_to_use} was modified without a rev bump — delete and re-import")
            return rev_to_use
        else:
            rev_to_use = latest_rev
    else:
        # === Validate requested revision exists ===
        requested_path = os.path.join(base_path, f"{mpn}-rev{desired_rev}")
        if not os.path.exists(requested_path):
            print(f"{item_name:<24}  requested rev {desired_rev} does not exist")
            return None

        if int(latest_rev) > int(desired_rev):
            print(f"{item_name:<24}  newer rev available (rev{latest_rev}), you currently have (rev{desired_rev})")
            return latest_rev

        rev_to_use = desired_rev

    # === Paths for source and target ===
    source_lib_path = os.path.join(base_path, f"{mpn}-rev{rev_to_use}")
    target_lib_path = os.path.join(destination_directory, "library_used_do_not_edit", f"{mpn}-rev{rev_to_use}")

    # === Import logic ===
    if not os.path.exists(target_lib_path):
        shutil.copytree(source_lib_path, target_lib_path)
        status = f"imported rev {rev_to_use}"

        # === Copy selected editable files on fresh import only ===
        rename_suffixes = [
            "-drawing.svg",
            "-params.json",
            "-attributes.json"
        ]

        for filename in os.listdir(source_lib_path):
            src_file = os.path.join(source_lib_path, filename)
            if not os.path.isfile(src_file):
                continue

            # Determine destination name
            new_name = filename
            for suffix in rename_suffixes:
                if filename.endswith(suffix):
                    new_name = f"{item_name}{suffix}"
                    break

            dst_file = os.path.join(destination_directory, new_name)
            shutil.copy2(src_file, dst_file)

            # Patch group IDs in SVG
            if new_name.endswith(".svg"):
                with open(dst_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                content = content.replace(
                    f"{mpn}-drawing-contents-start", f"{item_name}-contents-start"
                ).replace(
                    f"{mpn}-drawing-contents-end", f"{item_name}-contents-end"
                )
                with open(dst_file, 'w', encoding='utf-8') as f:
                    f.write(content)
    else:
        if not find_modifications(source_lib_path, target_lib_path):
            status = f"up to date (rev{rev_to_use})"
            print(f"{item_name:<24}  {status}")
        else:
            raise RuntimeError(f"{item_name}: local copy of rev {rev_to_use} was modified without a rev bump — delete and re-import")

    return rev_to_use

def pull_parts():
    print()
    print("Importing from library")
    print(f"{"ITEM NAME":<24}  STATUS")
    load_dotenv()
    supported_library_components = ['connector', 'backshell']
    instances = instances_list.read_instance_rows()

    for instance in instances:
        item_type = instance.get('item_type', '').lower()
        item_name = instance.get('instance_name')
        if item_type not in supported_library_components:
            print(f"{item_name:<24}  item type '{item_type}' not in library")
            continue

        supplier = instance.get('supplier')
        mpn = instance.get('mpn', '')
        destination_directory = os.path.join(fileio.dirpath("editable_component_data"), item_name)

        # Determine rev from existing folders
        revs_found = []
        lib_used_path = os.path.join(destination_directory, "library_used_do_not_edit")
        if os.path.exists(lib_used_path):
            for entry in os.listdir(lib_used_path):
                match = re.fullmatch(rf"{re.escape(mpn)}-rev(\d+)", entry)
                if match:
                    revs_found.append(int(match.group(1)))

        desired_rev = str(max(revs_found)) if revs_found else "latest"
        used_rev = desired_rev if desired_rev != "latest" else None

        returned_rev = pull_item_from_library(
            supplier=supplier,
            lib_subpath="parts",
            mpn=mpn,
            desired_rev=desired_rev,
            destination_directory=destination_directory,
            used_rev=used_rev,
            item_name=item_name
        )
        
        if desired_rev == "latest" and used_rev is None:
            print(f"{item_name:<24}  no rev folder found; importing latest from library (rev{returned_rev})")

        if returned_rev is not None:
            instances_list.add_lib_latest_rev(item_name, returned_rev)
            if desired_rev != "latest":
                instances_list.add_lib_used_rev(item_name, desired_rev)
            else:
                instances_list.add_lib_used_rev(item_name, returned_rev)

def exists_in_lib_used(instance_name, mpn):
    # Look for revision folders inside library_used/<instance_name>/
    base_path = os.path.join(fileio.dirpath("editable_component_data"), instance_name, "library_used_do_not_edit")

    try:
        for name in os.listdir(base_path):
            full_path = os.path.join(base_path, name)
            if os.path.isdir(full_path) and name.startswith(mpn):
                match = re.search(r'rev(\d+)', name, re.IGNORECASE)
                if match:
                    instances_list.add_lib_used_earliest_rev(instance_name, match.group(1))
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