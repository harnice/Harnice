import os
import os.path
import datetime
import shutil
import re
import csv
from harnice import cli
from harnice.lists import rev_history

# standard punctuation:
#  .  separates between name hierarchy levels
#  _  means nothing, basically a space character
#  -  if multiple instances are found at the same hierarchy level with the same name,
# this separates name from unique instance identifier

product_type = ""
net = ""

pn = ""
rev = 0


def part_directory():
    return os.path.dirname(os.getcwd())


def rev_directory():
    return os.getcwd()


def set_product_type(x):
    global product_type
    product_type = x


def set_net(x):
    global net
    net = x


def get_net():
    return net


def partnumber(format):
    # Returns part numbers in various formats based on the current working directory

    # given a part number "pppppp-revR"

    # format options:
    # pn-rev:    returns "pppppp-revR"
    # pn:        returns "pppppp"
    # rev:       returns "revR"
    # R:         returns "R"

    pn_rev = os.path.basename(rev_directory())

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
            f"{partnumber('pn-rev')}-formboard_graph_definition.png": "formboard graph definition png",
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
            "features_for_relatives": {},
            "harnesses": {},
            "lists": {
                f"{partnumber('pn-rev')}-bom.tsv": "bom",
                f"{partnumber('pn-rev')}-circuits_list.tsv": "circuits list",
                f"{partnumber('pn-rev')}-post_harness_instances_list.tsv": "post harness instances list",
                f"{partnumber('pn-rev')}-system_manifest.tsv": "system manifest",
                f"{partnumber('pn-rev')}-system_connector_list.tsv": "system connector list",
                f"{partnumber('pn-rev')}-mapped_channels_set.tsv": "mapped channels set",
                f"{partnumber('pn-rev')}-mapped_disconnect_channels_set.tsv": "mapped disconnects set",
                f"{partnumber('pn-rev')}-mapped_a_channels_through_disconnects_set.tsv": "mapped A-side channels through disconnects set",
            },
            "macros": {},
            "maps": {
                f"{partnumber('pn-rev')}-channel_map.tsv": "channel map",
                f"{partnumber('pn-rev')}-disconnect_map.tsv": "disconnect map",
            },
        }
    elif product_type == "cable":
        return {
            f"{partnumber('pn-rev')}-attributes.json": "attributes",
            f"{partnumber('pn-rev')}-conductor_list.tsv": "conductor list",
        }
    else:
        raise ValueError(f"Invalid product type: {product_type}")


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
        os.makedirs(dirpath("features_for_relatives"), exist_ok=True)
        os.makedirs(dirpath("harnesses"), exist_ok=True)
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
    # FILES NOT DEPENDENT ON PRODUCT TYPE
    if target_value == "revision history":
        file_path = os.path.join(
            part_directory(), f"{partnumber('pn')}-revision_history.tsv"
        )
        return file_path

    # FILES DEPENDENT ON HARNICE ROOT

    if target_value == "library locations":
        import harnice

        harnice_root = os.path.dirname(
            os.path.dirname(os.path.dirname(harnice.__file__))
        )
        return os.path.join(harnice_root, "library_locations.csv")

    if target_value == "project locations":
        import harnice

        harnice_root = os.path.dirname(
            os.path.dirname(os.path.dirname(harnice.__file__))
        )
        return os.path.join(harnice_root, "project_locations.csv")

    # FILES OUTSIDE OF PRODUCT DIRECTORY
    if product_type == "device":
        if target_value == "library file":
            return os.path.join(dirpath("kicad"), f"{partnumber('pn')}.kicad_sym")

        if target_value == "library setup info":
            return os.path.join(dirpath("kicad"), "librarybasics.txt")

    # FILES INSIDE OF A STRUCURE DEFINED BY FILEIO
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
    return os.path.join(rev_directory(), *path_value)


def dirpath(target_key):
    # returns the path of a directory you know the name of. use that directory name as the argument.
    if product_type == "device":
        if target_key == "kicad":
            return os.path.join(part_directory(), "kicad")

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
    return os.path.join(rev_directory(), *path_key)


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
        rows = read_tsv(filepath)
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

        for row in read_tsv("library locations", delimiter=","):
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

    # if everything looks good but the tsv isn't there
    x = rev_history.current_info()
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


def get_path_to_project(traceable_key):
    # takes in a project repo traceable key and returns the expanded local path
    # traceable key is some unique identifier for this project (project part number, github url, etc)

    for project in read_tsv("project locations", delimiter=","):
        if project.get("traceable_key").strip() == traceable_key.strip():
            local_path = project.get("local_path")
            if not local_path:
                raise ValueError(f"No project local path found for {traceable_key}")
            return os.path.expanduser(local_path)

    raise ValueError(f"Could not find library repo id {traceable_key}")


def newrev():
    """
    Create a new revision directory by copying the current revision's contents
    and updating filenames to reflect the new revision number.
    """
    # Ensure revision structure is valid and get context
    verify_revision_structure()

    # Prompt user for new revision number
    new_rev_number = cli.prompt(
        f"Current rev number: {partnumber('R')}. Enter new rev number:",
        default=str(int(partnumber("R")) + 1),
    )

    # Construct new revision directory path
    new_rev_dir = os.path.join(
        part_directory(), f"{partnumber('pn')}-rev{new_rev_number}"
    )

    # Ensure target directory does not already exist
    if os.path.exists(new_rev_dir):
        raise FileExistsError(f"Revision directory already exists: {new_rev_dir}")

    shutil.copytree(rev_directory(), new_rev_dir)

    # Walk the new directory and rename all files containing the old rev number
    for root, _, files in os.walk(new_rev_dir):
        for filename in files:
            new_suffix = f"rev{new_rev_number}"

            if partnumber("rev") in filename:
                old_path = os.path.join(root, filename)
                new_name = filename.replace(partnumber("rev"), new_suffix)
                new_path = os.path.join(root, new_name)

                os.rename(old_path, new_path)

    print(
        f"Successfully created new revision: {partnumber('pn-rev')}. Please cd into it."
    )


def read_tsv(filekey, delimiter="\t"):
    try:
        path_to_open = path(filekey)
    except TypeError:
        path_to_open = filekey

    if not os.path.exists(path_to_open):
        raise FileNotFoundError(
            f"Expected tsv file with delimiter '{delimiter}' at: {path_to_open}"
        )
    with open(path_to_open, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter=delimiter))
