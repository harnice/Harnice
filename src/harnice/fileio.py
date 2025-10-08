import os
import os.path
import datetime
import shutil
import re
import csv
from harnice import rev_history, cli

# standard punctuation:
#  .  separates between name hierarchy levels
#  _  means nothing, basically a space character
#  -  if multiple instances are found at the same hierarchy level with the same name,
# this separates name from unique instance identifier

product_type = ""

pn = ""
rev = 0


def _part_directory():
    return os.path.dirname(os.getcwd())


def _rev_directory():
    return os.getcwd()


def set_product_type(x):
    global product_type
    product_type = x


def partnumber(format):
    # Returns part numbers in various formats based on the current working directory

    # given a part number "pppppp-revR"

    # format options:
    # pn-rev:    returns "pppppp-revR"
    # pn:        returns "pppppp"
    # rev:       returns "revR"
    # R:         returns "R"

    pn_rev = os.path.basename(_rev_directory())

    if format == "pn-rev":
        return pn_rev

    elif format == "pn":
        match = re.search(r"-rev", pn_rev)
        if match:
            return pn_rev[: match.start()]

    elif format == "rev":
        match = re.search(r"-rev", pn_rev)
        if match:
            return pn_rev[match.start() + 1 :]

    elif format == "R":
        match = re.search(r"-rev", pn_rev)
        if match:
            return pn_rev[match.start() + 4 :]

    else:
        raise ValueError("Function 'partnumber' not presented with a valid format")


def harnice_file_structure():
    # syntax:
    #   "filename": "filekey"

    # filename is the actual file name with a suffix
    # filekey is the shorthand reference for it with no suffix

    if product_type == "harness":
        return {
            f"{partnumber('pn-rev')}-feature_tree.py": "feature tree",
            f"{partnumber('pn-rev')}-instances_list.tsv": "instances list",
            f"{partnumber('pn-rev')}-formboard_graph_definition.svg": "formboard graph definition svg",
            "instance_data": {
                "imported_instances": {},
                "generated_instances_do_not_edit": {},
            },
            "interactive_files": {
                f"{partnumber('pn-rev')}.formboard_graph_definition.tsv": "formboard graph definition",
                f"{partnumber('pn-rev')}.flagnotes.tsv": "flagnotes manual",
            },
            "macros": {},
        }
    elif product_type == "part":
        return {
            f"{partnumber('pn-rev')}-drawing.svg": "drawing",
            f"{partnumber('pn-rev')}-attributes.json": "attributes",
        }
    elif product_type == "flagnote":
        return {
            f"{partnumber('pn-rev')}-params.json": "params",
            f"{partnumber('pn-rev')}-drawing.svg": "drawing",
        }
    elif product_type in ("tblock", "titleblock"):
        return {
            f"{partnumber('pn-rev')}-params.json": "params",
            f"{partnumber('pn-rev')}-drawing.svg": "drawing",
            f"{partnumber('pn-rev')}-attributes.json": "attributes",
        }
    elif product_type == "device":
        return {
            f"{partnumber('pn-rev')}-feature_tree.py": "feature tree",
            f"{partnumber('pn-rev')}-signals_list.tsv": "signals list",
            f"{partnumber('pn-rev')}-attributes.json": "attributes",
        }
    elif product_type == "disconnect":
        return {
            f"{partnumber('pn-rev')}-feature_tree.py": "feature tree",
            f"{partnumber('pn-rev')}-signals_list.tsv": "signals list",
            f"{partnumber('pn-rev')}-attributes.json": "attributes",
        }
    elif product_type == "system":
        return {
            f"{partnumber('pn-rev')}-feature_tree.py": "feature tree",
            f"{partnumber('pn-rev')}-instances_list.tsv": "instances list",
            "devices": {},
            "disconnects": {},
            "lists": {
                f"{partnumber('pn-rev')}-bom.tsv": "bom",
                f"{partnumber('pn-rev')}-circuits_list.tsv": "circuits list",
                f"{partnumber('pn-rev')}-system_connector_list.tsv": "system connector list",
            },
            "macros": {},
            "maps": {
                f"{partnumber('pn-rev')}-chmap.tsv": "channel map",
                f"{partnumber('pn-rev')}-disconnect_map.tsv": "disconnect map",
                "mapped_channels.txt": "mapped channels set",
                "mapped_disconnect_channels.txt": "mapped disconnect channels set",
            },
        }


def generate_structure():
    if product_type == "harness":
        os.makedirs(dirpath("instance_data"), exist_ok=True)
        os.makedirs(dirpath("imported_instances"), exist_ok=True)
        silentremove(dirpath("generated_instances_do_not_edit"))
        os.makedirs(dirpath("generated_instances_do_not_edit"), exist_ok=True)
        os.makedirs(dirpath("interactive_files"), exist_ok=True)
        os.makedirs(dirpath("macros"), exist_ok=True)
    if product_type == "device":
        os.makedirs(dirpath("kicad"), exist_ok=True)
    if product_type == "system":
        os.makedirs(dirpath("devices"), exist_ok=True)
        os.makedirs(dirpath("disconnects"), exist_ok=True)
        os.makedirs(dirpath("lists"), exist_ok=True)
        os.makedirs(dirpath("macros"), exist_ok=True)
        os.makedirs(dirpath("maps"), exist_ok=True)


def silentremove(filepath):
    if os.path.exists(filepath):
        if os.path.isfile(filepath) or os.path.islink(filepath):
            os.remove(filepath)  # remove file or symlink
        elif os.path.isdir(filepath):
            shutil.rmtree(filepath)  # remove directory and contents


def path(target_value):
    # returns the filepath/filename of a filekey.
    """
    Recursively searches for a value in a nested JSON structure and returns the path to the element containing that value.

    Args:
        target_value (str): The value to search for.

    Returns:
        list: A list of container names leading to the element containing the target value, or None if not found.
    """
    if target_value == "revision history":
        file_path = os.path.join(
            _part_directory(), f"{partnumber('pn')}-revision_history.tsv"
        )
        return file_path

    if target_value == "library locations":
        # TODO: HOW DO I MAKE THIS RETURN THE HARNICE INSTALL LOCATION?
        return "/Users/kenyonshutt/Documents/GitHub/harnice/library_locations.csv"

    if product_type == "device":
        if target_value == "library file":
            return os.path.join(dirpath("kicad"), f"{partnumber('pn')}.kicad_sym")

        if target_value == "library setup info":
            return os.path.join(dirpath("kicad"), "librarybasics.txt")

    def recursive_search(data, path):
        if isinstance(data, dict):
            for key, value in data.items():
                if value == target_value:
                    return path + [key]
                result = recursive_search(value, path + [key])
                if result:
                    return result
        elif isinstance(data, list):
            for index, item in enumerate(data):
                if item == target_value:
                    return path + [f"[{index}]"]
                result = recursive_search(item, path + [f"[{index}]"])
                if result:
                    return result
        return None

    path_value = recursive_search(harnice_file_structure(), [])
    if not path_value:
        raise TypeError(f"Could not find filepath of {target_value}.")
    return os.path.join(_rev_directory(), *path_value)


def dirpath(target_key):
    # returns the path of a directory you know the name of. use that directory name as the argument.
    if product_type == "device":
        if target_key == "kicad":
            return os.path.join(_part_directory(), "kicad")

    def recursive_search(data, path):
        if isinstance(data, dict):
            for key, value in data.items():
                if key == target_key:
                    return path + [key]
                result = recursive_search(value, path + [key])
                if result:
                    return result
        elif isinstance(data, list):
            for index, item in enumerate(data):
                result = recursive_search(item, path + [f"[{index}]"])
                if result:
                    return result
        return None

    path_key = recursive_search(harnice_file_structure(), [])
    if not path_key:
        raise TypeError(f"Could not find directory {target_key}.")
    return os.path.join(_rev_directory(), *path_key)


def name(target_value):
    # returns the filename of a filekey.
    """
    Recursively searches for a value in a nested JSON structure and returns the key containing that value.

    Args:
        target_value (str): The value to search for.

    Returns:
        str: The key containing the target value, or None if not found.
    """

    def recursive_search(data):
        if isinstance(data, dict):
            for key, value in data.items():
                if value == target_value:
                    return key
                result = recursive_search(value)
                if result:
                    return result
        elif isinstance(data, list):
            for item in data:
                result = recursive_search(item)
                if result:
                    return result
        return None

    if not recursive_search(harnice_file_structure()):
        raise TypeError(f"Could not find filename of key {target_value}.")

    return recursive_search(harnice_file_structure())


def verify_revision_structure(product_type=None):
    cwd = os.getcwd()
    cwd_name = os.path.basename(cwd)
    parent = os.path.basename(os.path.dirname(cwd))
    temp_tsv_path = os.path.join(os.getcwd(), f"{cwd_name}-revision_history.tsv")

    def is_revision_folder(name, parent_name):
        return (
            name.startswith(f"{parent_name}-rev") and name.split("-rev")[-1].isdigit()
        )

    def has_revision_folder_inside(path, pn):
        pattern = re.compile(rf"{re.escape(pn)}-rev\d+")
        return any(pattern.fullmatch(d) for d in os.listdir(path))

    def make_new_rev_tsv(filepath, pn, rev):
        columns = rev_history.revision_history_columns()
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=columns, delimiter="\t")
            writer.writeheader()
        append_revision_row(filepath, pn, rev)

    def append_revision_row(filepath, pn, rev):
        if not os.path.exists(filepath):
            return "file not found"

        with open(filepath, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f, delimiter="\t"))

        rev = int(rev)

        desc = ""
        if rev != 1:
            # find the highest revision in the table
            highest_existing_rev = max(
                int(row.get("rev", 0)) for row in rows if row.get("rev")
            )

            for row in rows:
                if int(row.get("rev", 0)) == highest_existing_rev:
                    desc = row.get("desc")
                    if row.get("status") in [None, ""]:
                        print(
                            f"Your existing highest revision ({highest_existing_rev}) has no status. Do you want to obsolete it?"
                        )
                        obsolete_message = cli.prompt(
                            "Type your message here, leave blank for 'OBSOLETE' message, or type 'n' to keep it blank.",
                            default="OBSOLETE",
                        )
                        if obsolete_message == "n":
                            obsolete_message = ""
                        row["status"] = obsolete_message  # ← modified here
                    break

        default_descs = {
            "harness": "HARNESS, DOES A, FOR B",
            "part": "COTS COMPONENT, SIZE, COLOR, etc.",
            "flagnote": "FLAGNOTE, PURPOSE",
            "tblock": "TITLEBLOCK, PAPER SIZE, DESIGN",
            "device": "DEVICE, FUNCTION, ATTRIBUTES, etc.",
            "system": "SYSTEM, SCOPE, etc.",
        }

        # fallback in case product_type isn't in dict
        default_desc = default_descs.get(product_type, "")

        if desc in [None, ""]:
            desc = cli.prompt(
                f"Enter a description of this {product_type}", default=default_desc
            )

        revisionupdates = "INITIAL RELEASE"
        if rev_history.initial_release_exists():
            revisionupdates = ""
        revisionupdates = cli.prompt(
            "Enter a description for this revision", default=revisionupdates
        )
        while not revisionupdates or not revisionupdates.strip():
            print("Revision updates can't be blank!")
            revisionupdates = cli.prompt(
                "Enter a description for this revision", default=None
            )

        # add lib_repo if filepath is found in library locations
        library_repo = ""
        library_subpath = ""
        cwd = str(os.getcwd()).lower().strip("~")

        with open(path("library locations"), newline="", encoding="utf-8") as f:
            lib_info_list = list(csv.DictReader(f, delimiter=","))

        for row in lib_info_list:
            local_path = str(row.get("local_path", "")).lower().strip("~")
            if local_path and local_path in cwd:
                library_repo = row.get("url")

                # keep only the portion AFTER local_path
                idx = cwd.find(local_path)
                remainder = cwd[idx + len(local_path) :].lstrip("/")
                parts = remainder.split("/")

                # find the part number in the path
                pn = str(partnumber("pn")).lower()
                if pn in parts:
                    pn_index = parts.index(pn)
                    core_parts = parts[:pn_index]  # everything before pn
                else:
                    core_parts = parts

                # build library_subpath and product
                if core_parts:
                    library_subpath = (
                        "/".join(core_parts[1:]) + "/" if len(core_parts) > 1 else ""
                    )  # strip out the first element (product type)
                else:
                    library_subpath = ""

                break

        ####

        rows.append(
            {
                "pn": pn,
                "rev": rev,
                "desc": desc,
                "status": "",
                "library_repo": library_repo,
                "product": product_type,
                "library_subpath": library_subpath,
                "datestarted": today(),
                "datemodified": today(),
                "revisionupdates": revisionupdates,
            }
        )

        columns = rev_history.revision_history_columns()
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=columns, delimiter="\t")
            writer.writeheader()
            writer.writerows(rows)

    def prompt_new_part(part_dir, pn):
        rev = int(cli.prompt("Enter revision number", default="1"))
        make_new_rev_tsv(temp_tsv_path, pn, rev)
        folder = os.path.join(part_dir, f"{pn}-rev{rev}")
        os.makedirs(folder, exist_ok=True)
        os.chdir(folder)
        return rev

    # 1) Already in a <PN>-revN folder?
    if is_revision_folder(cwd_name, parent):
        pn = parent
        rev = int(cwd_name.split("-rev")[-1])  # already in a rev folder

    # 2) In a part folder (has rev folders inside)?
    elif has_revision_folder_inside(cwd, cwd_name):
        print(f"This is a part folder ({cwd_name}).")
        print(
            f"Please `cd` into one of its revision subfolders (e.g. `{cwd_name}-rev1`) and rerun."
        )
        exit()  # cancels if not in a rev folder

    # 3) Unknown – offer to initialize a new PN here
    else:
        answer = cli.prompt(
            f"No revision structure detected in '{cwd_name}'. Create new PN here?",
            default="y",
        )
        if answer.lower() not in ("y", "yes", ""):
            exit()
        pn = cwd_name
        rev = prompt_new_part(cwd, pn)  # changes the cwd to the new rev folder

    # if everything looks good but the tsv isn't
    x = rev_history.revision_info()
    if x == "row not found":
        append_revision_row(path("revision history"), pn, rev)
    elif x == "file not found":
        make_new_rev_tsv(path("revision history"), pn, rev)

    # now we’re in a revision folder, with pn, rev, temp_tsv_path set
    if not rev_history.status(rev) == "":
        raise RuntimeError(
            f"Revision {rev} status is not clear. Harnice will only let you render revs with a blank status."
        )

    print(f"Working on PN: {pn}, Rev: {rev}")
    generate_structure()
    rev_history.update_datemodified()

    return pn, rev


def today():
    return datetime.date.today().strftime("%-m/%-d/%y")
