import os
import subprocess
from harnice import fileio

build_macro_mpn = "kicad_pro_to_bom"

# kicad headers (fields in KiCad schematic, including custom attributes)
BOM_FIELDS = ["Reference", "MFG", "MPN", "supplier", "supplier_subpath", "rev"]

# output headers (labels in TSV)
BOM_LABELS = ["device_ref_des", "MFG", "MPN", "supplier", "supplier_subpath", "rev"]


def path(target_value: str) -> str:
    if target_value == "kicad sch":
        return os.path.join(
            os.getcwd(), "kicad", f"{fileio.partnumber('pn-rev')}.kicad_sch"
        )
    raise KeyError(f"Filename {target_value} not found in {build_macro_mpn} file tree")


"""
Use KiCad CLI to export a BOM TSV from the schematic.
Includes columns defined in BOM_FIELDS (with BOM_LABELS as headers).
Always overwrites the BOM file.
"""
sch_path = path("kicad sch")
bom_path = fileio.path("bom")

cmd = [
    "kicad-cli",
    "sch",
    "export",
    "bom",
    sch_path,
    "--fields",
    ",".join(BOM_FIELDS),
    "--labels",
    ",".join(BOM_LABELS),
    "--output",
    bom_path,
    "--field-delimiter",
    "\t",
    "--string-delimiter",
    "",  # ensure no quotes in output
]

# Run silently
subprocess.run(cmd, check=True, capture_output=True)
