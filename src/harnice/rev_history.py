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
        raise FileNotFoundError(f"[ERROR] Revision history file not found: {rev_path}")

    with open(rev_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            if row.get("rev") == fileio.partnumber("R"):
                return {k: (v or "").strip() for k, v in row.items()}

    raise ValueError(f"[ERROR] No revision row found for rev '{fileio.partnumber('R')}' in revision history")

def status(rev):
    with open(fileio.path("revision history"), "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            if str(row.get("rev")) == str(rev):
                return row.get("status")

def initial_release_exists():
    with open(fileio.path("revision history"), "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            if str(row.get("revisionupdates")) =="INITIAL RELEASE":
                return True
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