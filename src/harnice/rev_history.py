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

def generate_revision_history_tsv():
    with open(fileio.path("revision history"), 'w', encoding="utf-8") as file:
        file.write('\t'.join(REVISION_HISTORY_COLUMNS) + '\n')

def append_new_row(rev):
    """
    Adds a row to the revision history TSV.
    Populates only a subset of columns using column names for mapping.
    """
    pn = fileio.partnumber("pn")

    if rev == 1:
        message = cli.prompt("Enter a message for this rev", default="Initial Release")
    else:
        message = cli.prompt("Enter a message for this rev")

    today_date = datetime.date.today().isoformat()

    # Construct row using dictionary with column names
    row_dict = {
        "pn": pn,
        "rev": rev,
        "datestarted": today_date,
        "revisionupdates": message
    }

    # Fill all columns in correct order
    row_values = [str(row_dict.get(col, "")) for col in REVISION_HISTORY_COLUMNS]

    with open(fileio.path("revision history"), 'a', encoding="utf-8") as file:
        file.write('\t'.join(row_values) + '\n')

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
