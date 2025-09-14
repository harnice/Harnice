import xml.etree.ElementTree as ET
import os
import csv
import re
import shutil
from harnice import(
    fileio,
    instances_list
)

def pull_item_from_library(supplier, lib_subpath, mpn, destination_directory, used_rev=None, item_name=None, quiet=True):
    load_dotenv()
    if not isinstance(supplier, str) or not supplier.strip():
        raise ValueError(f"when importing {mpn} 'supplier' must be a non-empty string. Got: {supplier}")
    if not isinstance(lib_subpath, str) or not lib_subpath.strip():
        raise ValueError(f"when importing {mpn} 'lib_subpath' must be a non-empty string. Got: {lib_subpath}")
    if not isinstance(mpn, str) or not mpn.strip():
        raise ValueError(f"'mpn' must be a non-empty string. Got: {mpn}")
    if not isinstance(destination_directory, str) or not destination_directory.strip():
        raise ValueError(f"when importing {mpn} 'destination_directory' must be a non-empty string. Got: {destination_directory}")

    if item_name == "":
        item_name = mpn

    supplier_root = os.getenv(supplier)
    if supplier_root is None:
        raise ValueError(f"Environment variable '{supplier}' is not set. Expected to find path for library root.")

    base_path = os.path.join(supplier_root, lib_subpath, mpn)
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
        raise FileNotFoundError(f"Library folder not found: {base_path}")

    revision_folders = [
        name for name in os.listdir(base_path)
        if os.path.isdir(os.path.join(base_path, name)) and re.fullmatch(rf"{re.escape(mpn)}-rev(\d+)", name)
    ]
    if not revision_folders:
        raise FileNotFoundError(f"No revision folders found for {mpn} in {base_path}")

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

    if not os.path.exists(source_lib_path):
        raise FileNotFoundError(f"Revision folder not found: {source_lib_path}")

    if os.path.exists(target_lib_path):
        shutil.rmtree(target_lib_path)

    shutil.copytree(source_lib_path, target_lib_path)

    # === Copy editable files only if not already present
    rename_suffixes = ["-drawing.svg", "-params.json", "-attributes.json"]

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

    if not quiet:
        print(f"{item_name:<24}  {status}")

    # === Load revision row from revision history TSV in source library ===
    revhistory_row = None
    revhistory_path = os.path.join(base_path, f"{mpn}-revision_history.tsv")
    if not os.path.exists(revhistory_path):
        raise FileNotFoundError(f"Expected revision history TSV at: {revhistory_path}")

    with open(revhistory_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            if row.get("rev", "").strip() == library_rev:
                revhistory_row = row
                break

    return library_rev, revhistory_row

def pull_part(instance_name):
    load_dotenv()
    supported_library_components = ['connector', 'backshell']
    instances = instances_list.read_instance_rows()

    for instance in instances:
        item_name = instance.get('instance_name')
        if not item_name == instance_name:
            continue

        item_type = instance.get('item_type', '').lower()
        supplier = instance.get('supplier')
        mpn = instance.get('mpn', '')
        destination_directory = os.path.join(fileio.dirpath("imported_instances"), item_name)

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

        instances_list.add_revhistory_of_imported_part(item_name, revhistory_row)

def unpack_channel_type_id(id_value):
    """
    Normalize channel_type_id into (int, str).

    Accepts:
        - Tuple like (5, "public")
        - String like "(5, 'public')" or "(5,\"public\")"
    Returns:
        (int, str)
    """
    # Case 1: already a tuple
    if isinstance(id_value, tuple):
        if len(id_value) != 2:
            raise ValueError(f"Invalid channel_type_id tuple: {id_value}")
        key, supplier = id_value
        return int(key), str(supplier).strip()

    # Case 2: string
    if isinstance(id_value, str):
        text = id_value.strip().strip("()")
        parts = [p.strip() for p in text.split(",")]
        if len(parts) != 2:
            raise ValueError(f"Invalid channel_type_id string: {id_value}")

        key_str, supplier_str = parts
        key = int(key_str)
        supplier = supplier_str.strip("'\"")
        return key, supplier

    raise TypeError(f"Unsupported channel_type_id type: {type(id_value)}")

def parse_library_locations(lib_repo, wanted_field):
    lib_info_list = []
    with open(fileio.path("library locations"), newline='', encoding='utf-8') as f:
        lib_info_list = list(csv.DictReader(f, delimiter=','))
    for lib in lib_info_list:
        if lib.get("id") == lib_repo:
            return lib.get(wanted_field)
    raise ValueError(f"Could not find library repo id {lib_repo}")

if __name__ == "__main__":
    print(parse_library_locations("public","local_path"))