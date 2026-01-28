import os
import subprocess
import csv
from harnice import fileio, state

build_macro_mpn = "kicad_pro_to_bom"

# kicad headers (fields in KiCad schematic, including custom attributes)
BOM_FIELDS = ["Reference", "MFG", "MPN", "lib_repo", "lib_subpath", "rev", "Disconnect"]

# output headers (labels in TSV)
BOM_LABELS = [
    "device_refdes",
    "MFG",
    "MPN",
    "lib_repo",
    "lib_subpath",
    "rev",
    "disconnect",
]


def file_structure():
    return {
        "kicad": {
            f"{state.partnumber('pn-rev')}.kicad_sch": "kicad sch",
        }
    }


"""
Use KiCad CLI to export a BOM TSV from the schematic.
Includes columns defined in BOM_FIELDS (with BOM_LABELS as headers).
Always overwrites the BOM file.
"""

if not os.path.isfile(fileio.path("kicad sch", structure_dict=file_structure())):
    raise FileNotFoundError(
        f"Schematic not found. Check your kicad sch exists at this name and location: \n{fileio.path('kicad sch', structure_dict=file_structure())}"
    )

cmd = [
    "kicad-cli",
    "sch",
    "export",
    "bom",
    fileio.path("kicad sch", structure_dict=file_structure()),
    "--fields",
    ",".join(BOM_FIELDS),
    "--labels",
    ",".join(BOM_LABELS),
    "--output",
    fileio.path("bom"),
    "--field-delimiter",
    "\t",
    "--string-delimiter",
    "",  # ensure no quotes in output
]

# Run silently
subprocess.run(cmd, check=True, capture_output=True)


# --- Correct disconnects with local if lib_repo is empty ---
bom_path = fileio.path("bom")

# Read TSV into list of dicts
with open(bom_path, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f, delimiter="\t")
    bom = list(reader)

for row in bom:
    row["device_refdes"] = row["device_refdes"].strip("?")

# Rewrite TSV
with open(bom_path, "w", encoding="utf-8", newline="") as f:
    fieldnames = BOM_LABELS
    writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")
    writer.writeheader()
    writer.writerows(bom)
