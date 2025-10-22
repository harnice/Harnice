import os
import csv
import re
import shutil
from harnice import fileio
from harnice.lists import instances_list


def pull_item_from_library(
    lib_repo,
    product,
    mpn,
    destination_directory,
    lib_subpath="",
    used_rev=None,
    item_name=None,
    quiet=True,
):
    if not isinstance(lib_repo, str) or not lib_repo.strip():
        raise ValueError(
            f"when importing {mpn} 'lib_repo' must be a non-empty string. Got: {lib_repo}"
        )
    if not isinstance(product, str) or not product.strip():
        raise ValueError(
            f"when importing {mpn} 'product' must be a non-empty string. Got: {product}"
        )
    if not isinstance(mpn, str) or not mpn.strip():
        raise ValueError(f"'mpn' must be a non-empty string. Got: {mpn}")
    if not isinstance(destination_directory, str) or not destination_directory.strip():
        raise ValueError(
            f"when importing {mpn} 'destination_directory' must be a non-empty string. Got: {destination_directory}"
        )

    if item_name == "":
        item_name = mpn

    lib_repo_root = os.path.expanduser(get_local_path(lib_repo))
    base_path = os.path.join(lib_repo_root, product, lib_subpath, mpn)
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
    revision_folders = [
        name
        for name in os.listdir(base_path)
        if os.path.isdir(os.path.join(base_path, name))
        and re.fullmatch(rf"{re.escape(mpn.lower())}-rev(\d+)", name.lower())
    ]
    if not revision_folders:
        raise FileNotFoundError(f"No revision folders found for {mpn} in {base_path}")

    library_rev = str(
        max(int(re.search(r"rev(\d+)", name).group(1)) for name in revision_folders)
    )

    # === Decide which rev to use (from local presence)
    if local_rev:
        rev_to_use = local_rev
        if int(library_rev) > int(local_rev):
            status = (
                f"newer rev exists   (rev{local_rev} used, rev{library_rev} available)"
            )
        else:
            status = f"library up to date (rev{local_rev})"
    else:
        rev_to_use = library_rev
        status = f"imported latest (rev{rev_to_use})"

    # === Import library contents freshly every time
    source_lib_path = os.path.join(base_path, f"{mpn}-rev{rev_to_use}")
    target_lib_path = os.path.join(lib_used_path, f"{mpn}-rev{rev_to_use}")
    os.makedirs(lib_used_path, exist_ok=True)

    if not os.path.exists(source_lib_path):
        raise FileNotFoundError(f"Revision folder not found: {source_lib_path}")

    if os.path.exists(target_lib_path):
        shutil.rmtree(target_lib_path)

    shutil.copytree(source_lib_path, target_lib_path)

    # === Copy editable files only if not already present
    rename_suffixes = [
        "-drawing.svg",
        "-params.json",
        "-attributes.json",
        "-signals_list.tsv",
        "-feature_tree.py",
        "-conductor_list.tsv",
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
                with open(dst_file, "r", encoding="utf-8") as f:
                    content = f.read()
                content = content.replace(
                    f"{mpn}-drawing-contents-start", f"{item_name}-contents-start"
                ).replace(f"{mpn}-drawing-contents-end", f"{item_name}-contents-end")
                with open(dst_file, "w", encoding="utf-8") as f:
                    f.write(content)

    if not quiet:
        print(f"{item_name:<24}  {status}")

    # === Load revision row from revision history TSV in source library ===
    revhistory_row = None
    revhistory_path = os.path.join(base_path, f"{mpn}-revision_history.tsv")

    for row in fileio.read_tsv(revhistory_path):
        if row.get("rev", "").strip() == library_rev:
            revhistory_row = row
            break

    return library_rev, revhistory_row


def pull_part(instance):
    mpn = instance.get("mpn", "")
    destination_directory = os.path.join(
        fileio.dirpath("imported_instances"), instance.get("instance_name")
    )

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

    try:
        returned_rev, revhistory_row = pull_item_from_library(
            lib_repo=instance.get("lib_repo"),
            product="parts",
            mpn=instance.get("mpn"),
            destination_directory=destination_directory,
            used_rev=used_rev,
            item_name=instance.get("instance_name"),
            quiet=False,
        )
    except ValueError as e:
        raise ValueError(
            f"While importing instance '{instance.get("instance_name")}': {e}"
        ) from e

    instances_list.add_revhistory_of_imported_part(
        instance.get("instance_name"), revhistory_row
    )


def get_local_path(lib_repo):
    for lib in fileio.read_tsv("library locations", delimiter=","):
        if lib.get("url") == lib_repo:
            local_path = lib.get("local_path")
            if not local_path:
                raise ValueError(f"No local_path found for {lib_repo}")
            return os.path.expanduser(local_path)

    raise ValueError(f"Could not find library repo id {lib_repo}")
