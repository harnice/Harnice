from harnice import fileio
import runpy
import os

system_render_instructions_default = """
from harnice import featuretree
featuretree.runprebuilder("kicad_pro_to_netlist_prebuilder", "public")
"""

def render():
    if not os.path.exists(fileio.path("system render instructions")):
        with open(fileio.path("system render instructions"), "w", encoding="utf-8") as f:
            f.write(system_render_instructions_default)

    runpy.run_path(fileio.path("system render instructions"))

    fileio.verify_revision_structure()