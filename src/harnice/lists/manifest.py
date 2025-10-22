import os
import csv
import shutil
from harnice import fileio

COLUMNS = ["net", "harness_pn"]


def new():
    """
    Synchronize the system manifest with the system connector list:
      - Remove nets that no longer exist in the connector list
      - Add nets that appear in the connector list but not yet in the manifest
      - Preserve all other column data for nets that still exist
    """
    # Load connector list and extract unique nets
    with open(fileio.path("system connector list"), newline="", encoding="utf-8") as f:
        connector_list = list(csv.DictReader(f, delimiter="\t"))
    connector_nets = {
        row.get("net", "").strip() for row in connector_list if row.get("net")
    }

    manifest_path = fileio.path("system manifest")

    # Load existing manifest if present
    existing_manifest = []
    manifest_nets = set()
    try:
        with open(manifest_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter="\t")
            existing_manifest = list(reader)
            manifest_nets = {
                row.get("net", "").strip()
                for row in existing_manifest
                if row.get("net")
            }
    except FileNotFoundError:
        existing_manifest = []
        manifest_nets = set()

    # Determine differences
    nets_to_add = connector_nets - manifest_nets
    nets_to_remove = manifest_nets - connector_nets
    nets_to_keep = manifest_nets & connector_nets

    # Preserve existing info for kept nets
    updated_manifest = [
        row for row in existing_manifest if row.get("net") in nets_to_keep
    ]

    # Add new rows for new nets
    for net in sorted(nets_to_add):
        updated_manifest.append({"net": net})

    # Sort by net name for consistency
    updated_manifest = sorted(updated_manifest, key=lambda r: r.get("net", ""))

    # Write updated manifest
    with open(manifest_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS, delimiter="\t")
        writer.writeheader()
        for row in updated_manifest:
            full_row = {col: row.get(col, "") for col in COLUMNS}
            writer.writerow(full_row)


def update_upstream(path_to_system_rev, system_pn_rev, manifest_nets, harness_pn):
    manifest_path = os.path.join(
        path_to_system_rev,
        "lists",
        f"{system_pn_rev[0]}-{system_pn_rev[1]}-system_manifest.tsv",
    )

    # Read existing manifest
    with open(manifest_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        manifest = list(reader)
        fieldnames = reader.fieldnames

    # --- Pass 1: update matching nets ---
    for net in manifest_nets:
        for row in manifest:
            if row.get("net") == net:
                row["harness_pn"] = harness_pn
                break

    # --- Pass 2: remove outdated links ---
    for row in manifest:
        if row.get("harness_pn") == harness_pn and row.get("net") not in manifest_nets:
            row["harness_pn"] = ""

    # Write back updated manifest
    with open(manifest_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        writer.writerows(manifest)
