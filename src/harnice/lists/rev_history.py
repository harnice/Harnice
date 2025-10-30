import os
import csv
from harnice import fileio, state

# === Global Columns Definition ===
COLUMNS = [
    "mfg",
    "pn",
    "desc",
    "rev",
    "status",
    "releaseticket",
    "library_repo",
    "product",
    "library_subpath",
    "datestarted",
    "datemodified",
    "datereleased",
    "drawnby",
    "checkedby",
    "revisionupdates",
    "affectedinstances",
]


def info(rev=None, path=None, field=None):
    if path is None:
        path = fileio.path("revision history")

    if not os.path.exists(path):
        return "file not found"  # exact text is looked up in downstream texts, don't make it more specific

    if rev:
        rev = str(rev)
    else:
        rev = state.partnumber("R")

    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        rows = list(reader)
        for row in rows:
            if row.get("rev") == rev:
                if field:
                    return row.get(field)
                else:
                    return row

    return "row not found"  # exact text is looked up in downstream texts, don't make it more specific


def initial_release_exists():
    for row in fileio.read_tsv(fileio.path("revision history")):
        if str(row.get("revisionupdates", "")).strip() == "INITIAL RELEASE":
            return True
        else:
            return False


def initial_release_desc():
    for row in fileio.read_tsv(fileio.path("revision history")):
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

    # Write back
    with open(
        fileio.path("revision history"), "w", newline="", encoding="utf-8"
    ) as f_out:
        writer = csv.DictWriter(f_out, fieldnames=COLUMNS, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def new(filepath, pn, rev):
    columns = COLUMNS
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns, delimiter="\t")
        writer.writeheader()
    append(filepath, pn, rev)


def append(filepath, pn, rev):
    from harnice import cli

    rows = fileio.read_tsv(filepath)
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
    default_desc = default_descs.get(state.product(), "")

    # TODO: #478
    if desc in [None, ""]:
        desc = cli.prompt(
            f"Enter a description of this {state.product()}", default=default_desc
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

    for row in fileio.read_tsv(fileio.path("library locations")):
        local_path = str(row.get("local_path", "")).lower().strip("~")
        if local_path and local_path in cwd:
            library_repo = row.get("url")

            # keep only the portion AFTER local_path
            idx = cwd.find(local_path)
            remainder = cwd[idx + len(local_path) :].lstrip("/")
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
            "pn": pn,
            "rev": rev,
            "desc": desc,
            "status": "",
            "library_repo": library_repo,
            "product": state.product(),
            "library_subpath": library_subpath,
            "datestarted": fileio.today(),
            "datemodified": fileio.today(),
            "revisionupdates": revisionupdates,
        }
    )

    columns = COLUMNS
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)
