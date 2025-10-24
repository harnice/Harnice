import os
import re
import shutil
from harnice import fileio
from harnice.lists import instances_list, rev_history

"""
imported_instances
    lib_subpath
        destination_directory
            lib_used
                lib_used_rev

"""


def pull(input_dict, update_instances_list=True):
    #throw errors if required fields are blank
    if input_dict.get("lib_repo") in [None, ""]:
        raise ValueError(f"when importing {input_dict.get('instance_name')} 'lib_repo' is required but blank")
    if input_dict.get("mpn") in [None, ""]:
        raise ValueError(f"when importing {input_dict.get('instance_name')} 'mpn' is required but blank")
    if input_dict.get("item_type") in [None, ""]:
        raise ValueError(f"when importing {input_dict.get('instance_name')} 'item_type' is required but blank")

    #determine destination directory
    destination_directory = os.path.join(fileio.dirpath("imported_instances"), input_dict.get("item_type"), input_dict.get("instance_name"))

    #determine source library path
    source_lib_path = os.path.join(get_local_path(input_dict.get("lib_repo")), input_dict.get("item_type"), input_dict.get("lib_subpath", ""), input_dict.get("mpn"))

    # === Find highest rev in library
    source_revision_folders = [
        name
        for name in os.listdir(source_lib_path)
        if os.path.isdir(os.path.join(source_lib_path, name))
        and re.fullmatch(rf"{re.escape(input_dict.get('mpn').lower())}-rev(\d+)", name.lower())
    ]
    if not source_revision_folders:
        raise FileNotFoundError(f"No revision folders found for {input_dict.get('mpn')} in {source_lib_path}")
    highest_source_rev = str(
        max(int(re.search(r"rev(\d+)", name).group(1)) for name in source_revision_folders)
    )
    # === Decide which rev to use
    if input_dict.get("lib_rev_used_here"):
        rev_to_use = int(input_dict.get("lib_rev_used_here").strip().lower().replace("rev", ""))
        if int(highest_source_rev) > int(rev_to_use):
            status = (
                f"newer rev exists   (rev{rev_to_use} used, rev{highest_source_rev} available)"
            )
        else:
            status = f"library up to date (rev{rev_to_use})"
    else:
        rev_to_use = highest_source_rev
        status = f"imported latest (rev{rev_to_use})"

    # === Import library contents freshly every time
    lib_used_path = os.path.join(destination_directory, "library_used_do_not_edit")
    os.makedirs(lib_used_path,exist_ok=True)
    
    lib_used_rev_path = os.path.join(lib_used_path, f"{input_dict.get('mpn')}-rev{rev_to_use}")
    if os.path.exists(lib_used_rev_path):
        shutil.rmtree(lib_used_rev_path)
    
    source_lib_rev_path = os.path.join(source_lib_path, f"{input_dict.get('mpn')}-rev{rev_to_use}")

    shutil.copytree(source_lib_rev_path, lib_used_rev_path)

    # === Copy editable files into the editable directory only if not already present
    rename_suffixes = [
        "-drawing.svg",
        "-params.json",
        "-attributes.json",
        "-signals_list.tsv",
        "-feature_tree.py",
        "-conductor_list.tsv",
    ]
    for filename in os.listdir(lib_used_rev_path):
        lib_used_do_not_edit_file = os.path.join(lib_used_rev_path, filename)

        new_name = filename
        for suffix in rename_suffixes:
            if filename.endswith(suffix):
                new_name = f"{input_dict.get('instance_name')}{suffix}"
                break

        editable_file_path = os.path.join(destination_directory, new_name)
        if not os.path.exists(editable_file_path):
            shutil.copy2(lib_used_do_not_edit_file, editable_file_path)

            #special rules for copying svg
            if new_name.endswith(".svg"):
                with open(editable_file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                content = content.replace(
                    f"{input_dict.get('mpn')}-drawing-contents-start", f"{input_dict.get('instance_name')}-contents-start"
                ).replace(f"{input_dict.get('mpn')}-drawing-contents-end", f"{input_dict.get('instance_name')}-contents-end")
                with open(editable_file_path, "w", encoding="utf-8") as f:
                    f.write(content)

    # === Load revision row from revision history TSV in source library ===
    revhistory_path = os.path.join(source_lib_path, f"{input_dict.get('mpn')}-revision_history.tsv")
    revhistory_row = rev_history.info(rev=rev_to_use, path=revhistory_path)

    if update_instances_list and not input_dict.get("item_type").strip().lower()=="macro":
        update_contents = {
            "item_type": input_dict.get("item_type"),
            "lib_desc": revhistory_row.get("desc"),
            "lib_latest_rev": highest_source_rev,
            "lib_rev_used_here": rev_to_use,
            "lib_status": revhistory_row.get("status"),
            "lib_releaseticket": revhistory_row.get("releaseticket"),
            "lib_datestarted": revhistory_row.get("datestarted"),
            "lib_datemodified": revhistory_row.get("datemodified"),
            "lib_datereleased": revhistory_row.get("datereleased"),
            "lib_drawnby": revhistory_row.get("drawnby"),
            "lib_checkedby": revhistory_row.get("checkedby"),
            "project_editable_lib_modified": "TODO"
        }

        try:
            instances_list.modify(input_dict.get("instance_name"),update_contents)
        except ValueError:
            instances_list.new_instance(input_dict.get("instance_name"), update_contents)
    
    print(f"Importing from library: {input_dict.get('instance_name'):<40}{input_dict.get('item_type'):<20}{status}")
    return destination_directory


def get_local_path(lib_repo):
    for lib in fileio.read_tsv("library locations", delimiter=","):
        if lib.get("url") == lib_repo:
            local_path = lib.get("local_path")
            if not local_path:
                raise ValueError(f"No local_path found for {lib_repo}")
            return os.path.expanduser(local_path)
