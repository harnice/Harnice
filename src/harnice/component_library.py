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
    instances_list
)

def pull_item_from_library(supplier, lib_subpath, mpn, destination_directory, used_rev=None, item_name=None, quiet=True):
    if item_name == "":
        item_name = mpn

    base_path = os.path.join(os.getenv(supplier), lib_subpath, mpn)
    lib_used_path = os.path.join(destination_directory, "library_used_do_not_edit")

    # === Find highest local rev
    revs_found = []
    if os.path.exists(lib_used_path):
        for name in os.listdir(lib_used_path):
            match = re.fullmatch(rf"{re.escape(mpn)}-rev(\d+)", name)
            if match:
                revs_found.append(int(match.group(1)))
    local_rev = str(max(revs_found)) if revs_found else None

    # === Find highest rev in library
    if not os.path.exists(base_path):
        print(f"{item_name:<24}  library folder missing")
        return None, None

    revision_folders = [
        name for name in os.listdir(base_path)
        if os.path.isdir(os.path.join(base_path, name)) and re.fullmatch(rf"{re.escape(mpn)}-rev(\d+)", name)
    ]
    if not revision_folders:
        print(f"{item_name:<24}  no revisions found in library")
        return None, None

    library_rev = str(max(int(re.search(r"rev(\d+)", name).group(1)) for name in revision_folders))

    # === Decide which rev to use (from local presence)
    if local_rev:
        rev_to_use = local_rev
        if int(library_rev) > int(local_rev):
            status = f"newer rev exists   (rev{local_rev} used, rev{library_rev} available)"
        else:
            status = f"library up to date (rev{local_rev})"
    else:
        rev_to_use = library_rev
        status = f"imported latest (rev{rev_to_use})"

    # === Import library contents freshly every time
    source_lib_path = os.path.join(base_path, f"{mpn}-rev{rev_to_use}")
    target_lib_path = os.path.join(lib_used_path, f"{mpn}-rev{rev_to_use}")
    os.makedirs(lib_used_path, exist_ok=True)

    if os.path.exists(target_lib_path):
        shutil.rmtree(target_lib_path)

    shutil.copytree(source_lib_path, target_lib_path)

    # === Copy editable files only if not already present
    rename_suffixes = [
        "-drawing.svg",
        "-params.json",
        "-attributes.json"
    ]

    for filename in os.listdir(source_lib_path):
        src_file = os.path.join(source_lib_path, filename)
        if not os.path.isfile(src_file):
            continue

        new_name = filename
        for suffix in rename_suffixes:
            if filename.endswith(suffix):
                new_name = f"{item_name}{suffix}"
                break

        dst_file = os.path.join(destination_directory, new_name)
        if not os.path.exists(dst_file):
            shutil.copy2(src_file, dst_file)

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

    if not quiet == True:
        print(f"{item_name:<24}  {status}")

    # === Load revision row from revision history TSV in source library ===
    revhistory_row = None
    revhistory_path = os.path.join(base_path, f"{mpn}-revision_history.tsv")
    with open(revhistory_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            if row.get("rev", "").strip() == library_rev:
                revhistory_row = row
                break

    return library_rev, revhistory_row

def pull_parts():
    print()
    print("Importing parts from library")
    print(f"{"ITEM NAME":<24}  STATUS")
    load_dotenv()
    supported_library_components = ['connector', 'backshell']
    instances = instances_list.read_instance_rows()

    for instance in instances:
        item_type = instance.get('item_type', '').lower()
        item_name = instance.get('instance_name')
        if item_type not in supported_library_components:
            print(f"{item_name:<24}  item type '{item_type}' not yet carried in library")
            continue

        supplier = instance.get('supplier')
        mpn = instance.get('mpn', '')
        destination_directory = os.path.join(fileio.dirpath("editable_instance_data"), item_name)

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

        returned_rev, revhistory_row = pull_item_from_library(
            supplier=supplier,
            lib_subpath="parts",
            mpn=mpn,
            destination_directory=destination_directory,
            used_rev=used_rev,
            item_name=item_name,
            quiet=False
        )

        instances_list.add_lib_latest_rev(item_name, returned_rev)
        instances_list.add_lib_used_rev(item_name, used_rev)