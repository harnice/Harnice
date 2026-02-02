import os
import csv
import ast
import importlib
from harnice import fileio, state

# === Global Columns Definition ===
COLUMNS = [
    "product", # the harnice product type (e.g. "harness", "connector", "device", "system", "macro", "flagnote", "tblock")
    "mfg", # who manufactures this product (blank ok)
    "pn", # name, part number, other identifier of this part. mfg+mpn combination must be unique within the library.
    "desc", # a brief description of this product
    "rev", # the revision of the part
    "status", # "released", "obsolete", etc. Harnice will not render a revision if the status has text in this field as a form of protection. 
    "releaseticket", # many companies do this, but it's not required.
    "library_repo", # auto-filled on render if the current working directory is discovered to be a library repository.
    "library_subpath", # auto-filled on render if in a library repository, this is the chain of directories between the product type and the part number
    "datestarted", # auto-filled to be the date when this part was first intialized
    "datemodified", # updates to today's date upon rendering
    "datereleased", # up to user to fill in as needed
    "git_hash_of_harnice_src", # auto-filled, git hash of the harnice source code during the latest render
    "drawnby", # auto-filled, the person who created the part
    "checkedby", # the person who checked the part, blank ok
    "revisionupdates", # a brief description of the changes made to this revision
    "affectedinstances", # the instance names of the instances that were affected by this revision. can be referenced later by PDF builders and more.
]


def overwrite(content_dict):
    PROTECTED_KEYS = [
        "product",
        "mfg",
        "pn",
        "rev",
        "releaseticket",
        "library_repo",
        "library_subpath",
        "datestarted",
    ]
    # 1) Ensure no unknown keys
    for key in content_dict:
        if key not in COLUMNS:
            raise KeyError(
                f"Harnice does not allow writing unknown key '{key}'. "
                f"Valid columns: {', '.join(COLUMNS)}"
            )

    # 2) Ensure none of the protected keys are being modified
    for key in PROTECTED_KEYS:
        if key in content_dict:
            raise KeyError(
                f"Harnice does not allow overwriting '{key}' by script.\n"
                f"Please edit the revision history manually."
            )

    # 3) Load or create revision history
    path = fileio.path("revision history")
    if not os.path.exists(path):
        new()  # Creates a blank rev history with header

    rows = fileio.read_tsv("revision history")

    # 4) Determine which revision we are updating from state
    target_rev = str(state.rev).strip()
    if not target_rev:
        raise RuntimeError("state.rev is not set. Did verify_revision_structure() run?")

    # 5) Update matching row
    found = False
    for row in rows:
        if str(row.get("rev", "")).strip() == target_rev:
            found = True
            for key, value in content_dict.items():
                row[key] = value

    if not found:
        raise ValueError(f"No revision '{target_rev}' found in revision history.")

    # 6) Write updated TSV
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def info(rev=None, path=None, field=None, all=False):
    if path is None:
        path = fileio.path("revision history")

    if not os.path.exists(path):
        raise FileNotFoundError(f"Revision history file not found at {path}")

    if rev:
        rev = str(rev)
    else:
        rev = state.partnumber("R")

    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        rows = list(reader)

    if all:
        return rows

    for row in rows:
        if row.get("rev") == rev:

            # ------------------------------------------------------
            # Field requested
            # ------------------------------------------------------
            if field:
                val = row.get(field)

                if field == "affectedinstances":
                    if not val or val.strip() == "":
                        return []
                    try:
                        return ast.literal_eval(val)
                    except Exception:
                        # fallback: return empty list if malformed
                        return []

                # other fields unchanged
                return val

            # ------------------------------------------------------
            # Entire row requested: parse affectedinstances only
            # ------------------------------------------------------
            full_row = dict(row)
            ai = row.get("affectedinstances")
            if ai and ai.strip() != "":
                try:
                    full_row["affectedinstances"] = ast.literal_eval(ai)
                except Exception:
                    full_row["affectedinstances"] = []
            else:
                full_row["affectedinstances"] = []

            return full_row

    raise ValueError(f"Revision {rev} not found in revision history at {path}")


def initial_release_exists():
    try:
        for row in fileio.read_tsv("revision history"):
            if str(row.get("revisionupdates", "")).strip() == "INITIAL RELEASE":
                return True
            else:
                return False
    except NameError:
        return False


def initial_release_desc():
    for row in fileio.read_tsv("revision history"):
        if row.get("revisionupdates") == "INITIAL RELEASE":
            return row.get("desc")


def update_datemodified():
    target_rev = state.partnumber("R")

    # Read all rows
    with open(fileio.path("revision history"), newline="", encoding="utf-8") as f_in:
        reader = csv.DictReader(f_in, delimiter="\t")
        rows = list(reader)

    # Modify matching row(s)
    for row in rows:
        if row.get("rev", "").strip() == target_rev:
            row["datemodified"] = fileio.today()
            row["drawnby"] = fileio.drawnby()["name"]
            row["git_hash_of_harnice_src"] = fileio.get_git_hash_of_harnice_src()

    # Write back
    with open(
        fileio.path("revision history"), "w", newline="", encoding="utf-8"
    ) as f_out:
        writer = csv.DictWriter(f_out, fieldnames=COLUMNS, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def new(ignore_product=False):
    columns = COLUMNS

    if not ignore_product:
        from harnice.cli import select_product_type
        global product
        product = select_product_type()

    if not os.path.exists(fileio.path("revision history")):
        with open(fileio.path("revision history"), "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=columns, delimiter="\t")
            writer.writeheader()

    else:
        raise ValueError("You tried to overwrite a revision history file- this is not allowed.")


def append(next_rev=None):
    from harnice import cli

    global product

    if not os.path.exists(fileio.path("revision history")):
        new()
    rows = fileio.read_tsv("revision history")
    product_name = None
    if rows:
        for row in reversed(rows):
            candidate = (row.get("product") or "").strip()
            if candidate:
                product_name = candidate
                break
    if not product_name:
        product_name = globals().get("product")
    if not product_name:
        product_name = cli.select_product_type()
    product = product_name

    default_desc = ""
    if product_name:
        try:
            product_module = importlib.import_module(f"harnice.products.{product_name}")
        except ModuleNotFoundError:
            product_module = None
        else:
            default_desc = getattr(product_module, "default_desc", "") or ""

    desc = ""
    if next_rev != 1:
        # find the highest revision in the table
        try:
            highest_existing_rev = max(
                int(row.get("rev", 0)) for row in rows if row.get("rev")
            )
        except ValueError:
            highest_existing_rev = None

        if next_rev != highest_existing_rev:
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

    if desc in [None, ""]:
        desc = cli.prompt(
            f"Enter a description of this {product_name}",
            default=default_desc,
        )

    revisionupdates = "INITIAL RELEASE"
    if initial_release_exists():
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

    for row in fileio.read_tsv("library locations", delimiter=","):
        lib_local_path = str(row.get("local_path", "")).lower().strip("~")
        if lib_local_path in cwd:
            library_repo = row.get("repo_url")

            # keep only the portion AFTER local_path
            idx = cwd.find(lib_local_path)
            remainder = cwd[idx + len(lib_local_path) :].lstrip("/")
            parts = remainder.split("/")

            # find the part number in the path
            pn = str(state.partnumber("pn")).lower()
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
            "product": product_name,
            "pn": state.pn,
            "rev": next_rev,
            "desc": desc,
            "status": "",
            "library_repo": library_repo,
            "library_subpath": library_subpath,
            "datestarted": fileio.today(),
            "datemodified": fileio.today(),
            "revisionupdates": revisionupdates,
        }
    )

    columns = COLUMNS
    with open(fileio.path("revision history"), "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)
