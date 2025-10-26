import os
import subprocess
from harnice import fileio

build_macro_mpn = "kicad_pro_to_pdf"

def file_structure():
    return {
        "instance_data":{
            "imported instances":{
                "Macro":{
                    artifact_id:{
                        f"{fileio.partnumber('pn-rev')}-{artifact_id}-kicad_sch.kicad_sch": "kicad sch",
                    }
                }
            }
        },
        f"{fileio.partnumber('pn-rev')}-{artifact_id}.pdf": "schematic pdf"
    }


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
