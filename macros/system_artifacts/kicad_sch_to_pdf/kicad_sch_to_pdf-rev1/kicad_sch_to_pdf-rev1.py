import os
import subprocess
from harnice import fileio

build_macro_mpn = "kicad_pro_to_pdf"


def path(target_value: str) -> str:
    if target_value == "kicad sch":
        return os.path.join(
            os.getcwd(), "kicad", f"{fileio.partnumber('pn-rev')}.kicad_sch"
        )
    if target_value == "schematic pdf":
        return os.path.join(
            artifact_path, f"{fileio.partnumber('pn-rev')}-{artifact_id}.pdf"
        )
    raise KeyError(f"Filename {target_value} not found in {build_macro_mpn} file tree")


"""
Use KiCad CLI to export the schematic as a PDF.
Always overwrites the existing PDF.
"""

if not os.path.isfile(path("kicad sch")):
    raise FileNotFoundError(
        f"Schematic not found. Check your kicad sch exists at this name and location:\n{path('kicad sch')}"
    )

cmd = [
    "kicad-cli",
    "sch",
    "export",
    "pdf",
    "--output",
    path("schematic pdf"),
    path("kicad sch"),
]

# Run silently
subprocess.run(cmd, check=True, capture_output=True)