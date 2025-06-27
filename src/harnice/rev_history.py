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
    pass
    """
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        rows = list(csv.DictReader(f, delimiter='\t'))
        fieldnames = reader.fieldnames

    for row in rows:
        if row.get("rev") == fileio.partnumber("rev"):
        #TODO: UPDATE THE MODIFIED KEY FOR THIS ROW
    
    with open(path, "w", newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter='\t')
        writer.writeheader()
        writer.writerows(rows)
    """