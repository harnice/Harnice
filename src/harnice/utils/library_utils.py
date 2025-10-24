import os
import re
import shutil
from harnice import fileio
from harnice.lists import instances_list, rev_history


def pull_instance(instance):
    #throw errors if required fields are blank
    if instance.get("lib_repo") in [None, ""]:
        raise ValueError(f"when importing {instance.get('instance_name')} 'lib_repo' is required but blank")
    if instance.get("mpn") in [None, ""]:
        raise ValueError(f"when importing {instance.get('instance_name')} 'mpn' is required but blank")
    if instance.get("item_type") in [None, ""]:
        raise ValueError(f"when importing {instance.get('instance_name')} 'item_type' is required but blank")

    #determine destination directory
    destination_directory = os.path.join(fileio.dirpath("imported_instances"), instance.get("item_type"), instance.get("lib_subpath", ""), instance.get("instance_name"))
    lib_used_path = os.path.join(destination_directory, "library_used_do_not_edit")

    #determine source library path
    source_lib_path = os.path.join(get_local_path(instance.get("lib_repo")), instance.get("item_type"), instance.get("lib_subpath", ""), instance.get("mpn"))

    # === Find highest rev in library
    source_revision_folders = [
        name
        for name in os.listdir(source_lib_path)
        if os.path.isdir(os.path.join(source_lib_path, name))
        and re.fullmatch(rf"{re.escape(instance.get('mpn').lower())}-rev(\d+)", name.lower())
    ]
    if not source_revision_folders:
        raise FileNotFoundError(f"No revision folders found for {instance.get('mpn')} in {source_lib_path}")
    highest_source_rev = str(
        max(int(re.search(r"rev(\d+)", name).group(1)) for name in source_revision_folders)
    )

    # === Decide which rev to use
    if instance.get("lib_rev_used_here"):
        rev_to_use = instance.get("lib_rev_used_here")
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
    source_lib_path = os.path.join(source_lib_path, f"{instance.get('mpn')}-rev{rev_to_use}")
    destination_lib_path = os.path.join(lib_used_path, f"{instance.get('mpn')}-rev{rev_to_use}")
    os.makedirs(lib_used_path, exist_ok=True)

    if os.path.exists(destination_lib_path):
        shutil.rmtree(destination_lib_path)

    shutil.copytree(source_lib_path, destination_lib_path)

    # === Copy editable files into the editable directory only if not already present
    rename_suffixes = [
        "-drawing.svg",
        "-params.json",
        "-attributes.json",
        "-signals_list.tsv",
        "-feature_tree.py",
        "-conductor_list.tsv",
    ]

    for filename in os.listdir(source_lib_path):
        lib_used_do_not_edit_file = os.path.join(source_lib_path, filename)
        if not os.path.isfile(lib_used_do_not_edit_file):
            continue

        new_name = filename
        for suffix in rename_suffixes:
            if filename.endswith(suffix):
                new_name = f"{instance.get('instance_name')}{suffix}"
                break

        editable_file = os.path.join(destination_directory, new_name)
        if not os.path.exists(editable_file):
            shutil.copy2(lib_used_do_not_edit_file, editable_file)

            #special rules for copying svg
            if new_name.endswith(".svg"):
                with open(editable_file, "r", encoding="utf-8") as f:
                    content = f.read()
                content = content.replace(
                    f"{instance.get('mpn')}-drawing-contents-start", f"{instance.get('instance_name')}-contents-start"
                ).replace(f"{instance.get('mpn')}-drawing-contents-end", f"{instance.get('instance_name')}-contents-end")
                with open(editable_file, "w", encoding="utf-8") as f:
                    f.write(content)

    # === Load revision row from revision history TSV in source library ===
    revhistory_path = os.path.join(source_lib_path, f"{instance.get('mpn')}-revision_history.tsv")

    revhistory_row = rev_history.info(rev=rev_to_use, path=revhistory_path)

    instances_list.modify(instance.get("instance_name"), {
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
    })


def get_local_path(lib_repo):
    for lib in fileio.read_tsv("library locations", delimiter=","):
        if lib.get("url") == lib_repo:
            local_path = lib.get("local_path")
            if not local_path:
                raise ValueError(f"No local_path found for {lib_repo}")
            return os.path.expanduser(local_path)
