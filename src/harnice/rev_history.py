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

def revision_history_columns():
    return REVISION_HISTORY_COLUMNS

def revision_info():
    rev_path = fileio.path("revision history")
    if not os.path.exists(rev_path):
        return "file not found"

    with open(rev_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            if row.get("rev") == fileio.partnumber("R"):
                return {k: (v or "").strip() for k, v in row.items()}

    return "row not found"

def status(rev):
    with open(fileio.path("revision history"), "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            if str(row.get("rev")) == str(rev):
                return row.get("status")

def initial_release_exists():
    try:
        with open(fileio.path("revision history"), "r", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter="\t")
            for row in reader:
                if str(row.get("revisionupdates")) =="INITIAL RELEASE":
                    return True
    except:
        return False

def initial_release_desc():
    try:
        with open(fileio.path("revision history"), "r", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter="\t")
            for row in reader:
                if row.get("revisionupdates") == "INITIAL RELEASE":
                    return row.get("desc")
    except:
        pass


def update_datemodified():
    today_str = datetime.date.today().isoformat()
    target_rev = fileio.partnumber("R")

    # Read all rows
    with open(fileio.path("revision history"), newline='', encoding='utf-8') as f_in:
        reader = csv.DictReader(f_in, delimiter='\t')
        rows = list(reader)

    # Modify matching row(s)
    for row in rows:
        print(f"!!!!{row.get("rev", "").strip()}...{target_rev}")
        if row.get("rev", "").strip() == target_rev:
            row["datemodified"] = today_str

    # Write back
    with open(fileio.path("revision history"), 'w', newline='', encoding='utf-8') as f_out:
        writer = csv.DictWriter(f_out, fieldnames=REVISION_HISTORY_COLUMNS, delimiter='\t')
        writer.writeheader()
        writer.writerows(rows)