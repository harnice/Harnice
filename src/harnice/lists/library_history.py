import csv
from harnice import fileio

COLUMNS = [
    "instance_name",
    "mpn",
    "item_type",
    "lib_repo",
    "lib_subpath",
    "lib_desc",
    "lib_latest_rev",
    "lib_rev_used_here",
    "lib_status",
    "lib_releaseticket",
    "lib_datestarted",
    "lib_datemodified",
    "lib_datereleased",
    "lib_drawnby",
    "lib_checkedby",
    "project_editable_lib_modified"
]

def new():
    with open(fileio.path("library history"), "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS, delimiter="\t")
        writer.writeheader()
        writer.writerows([])

def append(instance_name, instance_data):
    instance_data["instance_name"] = instance_name
    for row in fileio.read_tsv("library history"):
        if row.get("instance name") == instance_name:
            raise ValueError(f"You're trying to import something with instance_name '{instance_name}' but it has already been imported.")
    with open(fileio.path("library history"), "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS, delimiter="\t")
        writer.writerow({key: instance_data.get(key, "") for key in COLUMNS})