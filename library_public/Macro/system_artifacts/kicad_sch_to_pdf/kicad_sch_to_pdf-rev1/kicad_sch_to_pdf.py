import os
import subprocess
from harnice import fileio, state

build_macro_mpn = "kicad_pro_to_pdf"


def file_structure():
    return {
        "kicad": {
            f"{state.partnumber('pn-rev')}.kicad_sch": "kicad sch",
        },
        f"{state.partnumber('pn-rev')}-{artifact_id}.pdf": "schematic pdf",
    }


"""
Use KiCad CLI to export the schematic as a PDF.
Always overwrites the existing PDF.
"""

if not os.path.isfile(fileio.path("kicad sch", structure_dict=file_structure())):
    raise FileNotFoundError(
        f"Schematic not found. Check your kicad sch exists at this name and location:\n{fileio.path('kicad sch', structure_dict=file_structure())}"
    )

cmd = [
    "kicad-cli",
    "sch",
    "export",
    "pdf",
    "--output",
    fileio.path("schematic pdf", structure_dict=file_structure()),
    fileio.path("kicad sch", structure_dict=file_structure()),
]

# Run silently
subprocess.run(cmd, check=True, capture_output=True)
