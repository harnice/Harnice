import os
import re
import shutil
import filecmp
import json
from harnice import fileio
from harnice.lists import instances_list, library_history, rev_history
from harnice.cli import print_import_status

"""
where a part lands in a project after it's been imported:

instance_data
    item_type
        destination_directory
            lib_used
                lib_used_rev

"""


def pull(input_dict, update_instances_list=True, destination_directory=None):
    """
    Imports a part from the library into the project.

    Copies a part (device, connector, cable, etc.) from the library repository into
    the project's `instance_data` directory. Handles revision selection, file copying,
    and updating the instances list and library history. The function:

    1. Validates required fields (`lib_repo`, `mpn`, `item_type`)
    2. Determines which revision to use (specified or latest available)
    3. Copies the library revision to `library_used_do_not_edit`
    4. Copies editable files to the instance directory (only if not already present)
    5. Updates the instances list with library metadata
    6. Records the import in library history

    **Args:**
    - `input_dict` (dict): Dictionary containing part information with required keys:
        - `instance_name` (str): Name for this instance in the project
        - `lib_repo` (str): Library repository URL or `"local"` for local library
        - `mpn` (str): Manufacturer part number
        - `item_type` (str): Type of item (device, connector, cable, etc.)
        - `lib_subpath` (str, optional): Subpath within the library
        - `lib_rev_used_here` (str, optional): Specific revision to use (e.g., `"1"` or `"rev1"`)
    - `update_instances_list` (bool, optional): If `True`, updates the instances list with
        library metadata. Defaults to `True`.
    - `destination_directory` (str, optional): Custom destination directory. If `None`,
        defaults to `instance_data/{item_type}/{instance_name}`.

    **Returns:**
    - `str`: Path to the destination directory where the part was imported.

    **Raises:**
    - `ValueError`: If required fields (`lib_repo`, `mpn`, `item_type`) are blank.
    - `FileNotFoundError`: If no revision folders are found for the part number in the library.
    """
    # throw errors if required fields are blank
    if input_dict.get("lib_repo") in [None, ""]:
        raise ValueError(
            f"when importing {input_dict.get('instance_name')} 'lib_repo' is required but blank"
        )
    if input_dict.get("mpn") in [None, ""]:
        raise ValueError(
            f"when importing {input_dict.get('instance_name')} 'mpn' is required but blank"
        )
    if input_dict.get("item_type") in [None, ""]:
        raise ValueError(
            f"when importing {input_dict.get('instance_name')} 'item_type' is required but blank"
        )

    # determine destination directory
    if destination_directory is None:
        destination_directory = os.path.join(
            fileio.dirpath(None),
            "instance_data",
            input_dict.get("item_type"),
            input_dict.get("instance_name"),
        )
    os.makedirs(destination_directory, exist_ok=True)

    lib_repo = None
    if input_dict.get("lib_repo") == "local":
        lib_repo = os.path.join(fileio.part_directory(), "library")
    else:
        lib_repo = get_local_path(input_dict.get("lib_repo"))

    # determine source library path
    source_lib_path = os.path.join(
        lib_repo,
        input_dict.get("item_type"),
        input_dict.get("lib_subpath", ""),
        input_dict.get("mpn"),
    )

    # === Find highest rev in library
    source_revision_folders = [
        name
        for name in os.listdir(source_lib_path)
        if os.path.isdir(os.path.join(source_lib_path, name))
        and re.fullmatch(
            rf"{re.escape(input_dict.get('mpn').lower())}-rev(\d+)", name.lower()
        )
    ]
    if not source_revision_folders:
        raise FileNotFoundError(
            f"No revision folders found for {input_dict.get('mpn')} in {source_lib_path}"
        )
    highest_source_rev = str(
        max(
            int(re.search(r"rev(\d+)", name).group(1))
            for name in source_revision_folders
        )
    )
    # === Decide which rev to use
    if input_dict.get("lib_rev_used_here"):
        rev_to_use = int(
            input_dict.get("lib_rev_used_here").strip().lower().replace("rev", "")
        )
        if int(highest_source_rev) > int(rev_to_use):
            import_state = f"newer rev exists   (rev{rev_to_use} used, rev{highest_source_rev} available)"
        else:
            import_state = f"library up to date (rev{rev_to_use})"
    else:
        rev_to_use = highest_source_rev
        import_state = f"imported latest (rev{rev_to_use})"

    # === Import library contents freshly every time
    lib_used_path = os.path.join(destination_directory, "library_used_do_not_edit")
    os.makedirs(lib_used_path, exist_ok=True)

    lib_used_rev_path = os.path.join(
        lib_used_path, f"{input_dict.get('mpn')}-rev{rev_to_use}"
    )
    if os.path.exists(lib_used_rev_path):
        shutil.rmtree(lib_used_rev_path)

    source_lib_rev_path = os.path.join(
        source_lib_path, f"{input_dict.get('mpn')}-rev{rev_to_use}"
    )

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
    Modified = False
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

            # special rules for copying svg
            if new_name.endswith(".svg"):
                with open(editable_file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                content = content.replace(
                    f"{input_dict.get('mpn')}-drawing-contents-start",
                    f"{input_dict.get('instance_name')}-contents-start",
                ).replace(
                    f"{input_dict.get('mpn')}-drawing-contents-end",
                    f"{input_dict.get('instance_name')}-contents-end",
                )
                with open(editable_file_path, "w", encoding="utf-8") as f:
                    f.write(content)

        else:
            # Compare the existing editable file and the library version
            if not filecmp.cmp(
                lib_used_do_not_edit_file, editable_file_path, shallow=False
            ):
                Modified = Modified or True

    if Modified:
        import_state = f"modified in this project (rev{rev_to_use})"
    else:
        import_state = f"up to date (rev{rev_to_use})"

    # === Load revision row from revision history TSV in source library ===
    revhistory_path = os.path.join(
        source_lib_path, f"{input_dict.get('mpn')}-revision_history.tsv"
    )
    revhistory_row = rev_history.info(rev=rev_to_use, path=revhistory_path)

    try:
        with open(
            os.path.join(
                destination_directory,
                f"{input_dict.get('instance_name')}-attributes.json",
            ),
            "r",
            encoding="utf-8",
        ) as f:
            attributes_data = json.load(f)

        csys_children = attributes_data.get("csys_children") or {}
        tools = attributes_data.get("tools") or []
        build_notes = attributes_data.get("build_notes") or []

    except Exception:
        csys_children = {}
        tools = []
        build_notes = []

    update_contents = {
        "mpn": input_dict.get("mpn"),
        "item_type": input_dict.get("item_type"),
        "csys_children": csys_children,
        "lib_repo": lib_repo,
        "lib_subpath": input_dict.get("lib_subpath"),
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
        "lib_tools": tools,
        "lib_build_notes": build_notes,
        "project_editable_lib_modified": Modified,
    }

    if update_instances_list:
        try:
            instances_list.modify(input_dict.get("instance_name"), update_contents)
        except ValueError:
            instances_list.new_instance(
                input_dict.get("instance_name"), update_contents
            )

    library_history.append(input_dict.get("instance_name"), update_contents)

    print_import_status(
        input_dict.get("instance_name"),
        input_dict.get("item_type"),
        update_contents.get("lib_status"),
        import_state,
        os.path.basename(
            os.path.dirname(os.path.dirname(os.path.dirname(destination_directory)))
        ),
    )
    return destination_directory


def get_local_path(lib_repo):
    """
    Looks up the local filesystem path for a library repository URL.

    Reads the `library_locations.csv` file to find the mapping between a library
    repository URL and its local filesystem path. If the CSV file doesn't exist,
    it creates one with a default entry for the `harnice-library-public` repository.

    The lookup is case-insensitive. The local path is expanded (e.g., `~` is expanded
    to the user's home directory).

    **Args:**
    - `lib_repo` (str): Library repository URL to look up (e.g.,
        `"https://github.com/harnice/harnice"`).

    **Returns:**
    - `str`: Local filesystem path to the library repository.

    **Raises:**
    - `ValueError`: If the library repository URL is not found in the CSV file,
        or if no local path is specified for the repository.
    """
    csv_path = fileio.path("library locations")  # path to library_locations.csv

    # ----------------------------------------------------
    # If file does not exist, auto-generate with default
    # ----------------------------------------------------
    if not os.path.exists(csv_path):
        # Determine base directory of the Harnice repo
        # (__file__) → .../harnice/utils/library_utils.py
        # dirname 3 times → repo root
        repo_root = os.path.dirname(
            os.path.dirname(
                os.path.dirname(
                    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                )
            )
        )

        default_local_path = os.path.join(repo_root, "harnice-library-public")

        # Ensure the directory exists for the CSV
        os.makedirs(os.path.dirname(csv_path), exist_ok=True)

        with open(csv_path, "w", encoding="utf-8") as f:
            # Normalize the default path to ensure correct separators
            normalized_path = os.path.normpath(default_local_path)
            f.write(f"https://github.com/harnice/harnice,{normalized_path}\n")

        print(f"[harnice] Created '{csv_path}'")
        print(f"[harnice] Default library-public location: {default_local_path}")

    # ----------------------------------------------------
    # Normal lookup (with BOM-safe decoding)
    # ----------------------------------------------------
    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            parts = line.split(",")
            if len(parts) < 2:
                continue

            url = parts[0].strip()
            local = parts[1].strip()

            # Case-insensitive match
            if url.lower() == lib_repo.lower().strip():
                if not local:
                    raise ValueError(f"No local path found for '{lib_repo}'")
                # Expand user directory (~) and normalize path separators for current platform
                expanded_path = os.path.expanduser(local)
                # Normalize separators - os.path.normpath() converts forward slashes to
                # backslashes on Windows, ensuring proper path format
                return os.path.normpath(expanded_path)

    raise ValueError(f"'{lib_repo}' not found in library locations")
