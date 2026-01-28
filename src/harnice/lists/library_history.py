import csv
from harnice import fileio

COLUMNS = [
    "instance_name", #documentation needed
    "mpn", #documentation needed
    "item_type", #documentation needed
    "lib_repo", #documentation needed
    "lib_subpath", #documentation needed
    "lib_desc", #documentation needed
    "lib_latest_rev", #documentation needed
    "lib_rev_used_here", #documentation needed
    "lib_status", #documentation needed
    "lib_releaseticket", #documentation needed
    "lib_datestarted", #documentation needed
    "lib_datemodified", #documentation needed
    "lib_datereleased", #documentation needed
    "lib_drawnby", #documentation needed
    "lib_checkedby", #documentation needed
    "project_editable_lib_modified", #documentation needed
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
            raise ValueError(
                f"You're trying to import something with instance_name '{instance_name}' but it has already been imported."
            )
    with open(fileio.path("library history"), "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS, delimiter="\t")
        writer.writerow({key: instance_data.get(key, "") for key in COLUMNS})
