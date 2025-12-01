import os
import csv
import shutil
from harnice import fileio
from harnice.lists import instances_list

def rebuild():
    """
    Build the 'post harness instances list' by merging instance data from:
      - Each harness's instances list if the harness_pn is defined and file exists
      - Otherwise, fall back to the system-level instances list for matching nets

    Writes a clean TSV with INSTANCES_LIST_COLUMNS.
    """

    post_harness_instances = []

    # --- iterate through manifest rows ---
    for harness in fileio.read_tsv("harness manifest"):
        harness_pn = (harness.get("harness_pn") or "").strip()
        net = (harness.get("net") or "").strip()
        if not net:
            continue

        # Case 1: harness_pn missing -> import from system instances
        if not harness_pn:
            for system_instance in fileio.read_tsv("instances list"):
                if system_instance.get("net", "").strip() == net:
                    post_harness_instances.append(system_instance)
            continue

        # Case 2: harness_pn provided -> try to load harness instances list
        harness_instances_list_path = os.path.join(
            fileio.dirpath("harnesses"),
            f"{harness_pn}-instances_list.tsv",
        )

        if os.path.exists(harness_instances_list_path):
            post_harness_instances.extend(fileio.read_tsv(harness_instances_list_path))
        else:
            # Fallback to system-level instances for same net
            for system_instance in fileio.read_tsv("instances list"):
                if system_instance.get("net", "").strip() == net:
                    post_harness_instances.append(system_instance)

    # --- Determine fieldnames dynamically ---
    fieldnames = set()
    for instance in post_harness_instances:
        fieldnames.update(instance.keys())

    # --- Write TSV file ---
    with open(
        fileio.path("post harness instances list"), "w", newline="", encoding="utf-8"
    ) as f:
        writer = csv.DictWriter(f, fieldnames=instances_list.COLUMNS, delimiter="\t")
        writer.writeheader()
        for instance in post_harness_instances:
            writer.writerow({k: instance.get(k, "") for k in fieldnames})


def push(path_to_system_rev, system_pn_rev):
    path_to_harness_dir_of_system = os.path.join(
        path_to_system_rev, f"{system_pn_rev[0]}-{system_pn_rev[1]}", "harnesses"
    )
    shutil.copy(fileio.path("instances list"), path_to_harness_dir_of_system)
