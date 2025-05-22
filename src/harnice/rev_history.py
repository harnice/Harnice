import os
import re
import datetime
import json
import csv
from os.path import basename, dirname
from inspect import currentframe
from harnice import (
    fileio,
    cli
)

# === Global Columns Definition ===
REVISION_HISTORY_COLUMNS = [
    "pn", 
    "desc", 
    "rev", 
    "status", 
    "releaseticket", 
    "datestarted", 
    "datemodified", 
    "datereleased", 
    "drawnby", 
    "checkedby", 
    "revisionupdates", 
    "affectedinstances"
]

def read_revision_rows():
    with open(fileio.path("revision history"), newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f, delimiter='\t'))

def write_revision_rows(rows):
    with open(fileio.path("revision history"), 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=REVISION_HISTORY_COLUMNS, delimiter='\t')
        writer.writeheader()
        writer.writerows(rows)

def generate_revision_history_tsv():
    write_revision_rows([])

def append_new_row(rev):
    """
    Appends a new revision entry to the revision history TSV using the read/write revision rows pattern.
    """
    pn = fileio.partnumber("pn")
    today_date = datetime.date.today().isoformat()

    message = cli.prompt(
        "Enter a message for this rev", 
        default="Initial Release" if rev == 1 else None
    )

    # Create a new row using column-based mapping
    new_row = {col: "" for col in REVISION_HISTORY_COLUMNS}
    new_row["pn"] = pn
    new_row["rev"] = str(rev)
    new_row["datestarted"] = today_date
    new_row["revisionupdates"] = message

    # Read current rows, append the new row, and write back
    revisions = [r for r in read_revision_rows() if any(r.values())]
    revisions.append(new_row)
    write_revision_rows(revisions)
    
def revision_info():
    rev_path = fileio.path("revision history")
    if not os.path.exists(rev_path):
        raise FileNotFoundError(f"[ERROR] Revision history file not found: {rev_path}")

    with open(rev_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            if row.get("rev") == fileio.partnumber("R"):
                return {k: (v or "").strip() for k, v in row.items()}

    raise ValueError(f"[ERROR] No revision row found for rev '{fileio.partnumber('R')}' in revision history")
