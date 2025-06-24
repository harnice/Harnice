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
    import os
    import shutil
    import csv

    base_path = os.path.join(os.getenv(supplier), lib_subpath, mpn)
    source_lib_path = os.path.join(base_path, f"{mpn}-rev{desired_rev}")
    target_lib_path = os.path.join(destination_directory, "library_used_do_not_edit", f"{mpn}-rev{desired_rev}")

    # === Find latest rev from .revision_history.tsv ===
    latest_rev = ""
    rev_file = os.path.join(base_path, f"{mpn}.revision_history.tsv")
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
        print(f"Importing library '{item_name}': revision history missing.")
        return None

    # === Check source library folder exists ===
    if not os.path.exists(source_lib_path):
        print(f"Importing library '{item_name}': revision folder '{source_lib_path}' is missing.")
        return latest_rev

    # === Determine status ===
    latest = int(latest_rev)
    used = int(used_rev) if used_rev is not None else int(desired_rev)
    status = ""

    if not os.path.exists(target_lib_path):
        shutil.copytree(source_lib_path, target_lib_path)
        status = f"imported rev {desired_rev}"
    elif latest > used:
        status = f"newer rev available ({latest}); delete to re-import"
    elif latest < used:
        status = f"revision mismatch: used {used}, library {latest}"
    else:
        if not find_modifications(source_lib_path, target_lib_path):
            status = "up to date"
        else:
            status = f"modified without rev bump; delete and re-import"

    # === Copy all files (only if not already present) ===
    for filename in os.listdir(source_lib_path):
        src_file = os.path.join(source_lib_path, filename)
        dst_file = os.path.join(destination_directory, filename)

        if os.path.isfile(src_file) and not os.path.exists(dst_file):
            shutil.copy2(src_file, dst_file)

            # Patch contents group in SVG
            if filename.endswith(".svg"):
                with open(dst_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                content = content.replace(
                    f"{mpn}-drawing-contents-start", f"{mpn}-contents-start"
                ).replace(
                    f"{mpn}-drawing-contents-end", f"{mpn}-contents-end"
                )

                with open(dst_file, 'w', encoding='utf-8') as f:
                    f.write(content)

    print(f"Importing library '{item_name}': {status}")
    return latest_rev

def pull_parts():
    load_dotenv()
    supported_library_components = ['connector', 'backshell']
    instances = instances_list.read_instance_rows()
    updated_instances = []

    for instance in instances:
        item_type = instance.get('item_type', '').lower()
        if item_type not in supported_library_components:
            print(f"Library for '{instance.get('instance_name')}' with component type '{item_type}' either not needed or not supported")
            updated_instances.append(instance)
            continue

        supplier = instance.get('supplier')
        mpn = instance.get('mpn', '')
        item_name = instance.get('instance_name')
        destination_directory = os.path.join(fileio.dirpath("editable_component_data"), item_name)

        # Determine if already imported
        exists_bool, exists_rev = exists_in_lib_used(item_name, mpn)
        used_rev = exists_rev if exists_bool else None

        # === Pull from library ===
        desired_rev = instance.get('lib_latest_rev')  # Already prepopulated before?
        if not desired_rev:
            print(f"Library for '{item_name}' has no known desired_rev")
            updated_instances.append(instance)
            continue

        pull_item_from_library(
            supplier=supplier,
            lib_subpath="parts",
            mpn=mpn,
            desired_rev=desired_rev,
            destination_directory=destination_directory,
            used_rev=used_rev,
            item_name=item_name
        )

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