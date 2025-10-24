import os
import csv
from harnice import fileio

# === Global Columns Definition ===
REVISION_HISTORY_COLUMNS = [
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


def info(rev=None,path=fileio.path("revision history")):
    if not os.path.exists(path):
        return "file not found"

    if rev:
        rev = str(rev)
    else:
        rev = fileio.partnumber("R")

    for row in fileio.read_tsv(path):
        if row.get("rev") == rev:
            return row

    return f"rev row '{rev}' not found in '{path}'"


def initial_release_exists():
    for row in fileio.read_tsv("revision history"):
        if str(row.get("revisionupdates", "")).strip() == "INITIAL RELEASE":
            return True
        else:
            return False


def initial_release_desc():
    for row in fileio.read_tsv("revision history"):
        if row.get("revisionupdates") == "INITIAL RELEASE":
            return row.get("desc")


def update_datemodified():
    target_rev = fileio.partnumber("R")

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
        writer = csv.DictWriter(
            f_out, fieldnames=REVISION_HISTORY_COLUMNS, delimiter="\t"
        )
        writer.writeheader()
        writer.writerows(rows)
