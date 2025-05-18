import os
import time
import subprocess
import shutil
from os.path import basename
from inspect import currentframe
from harnice import(
    svg_utils,
    fileio
)

def generate_esch():
    # Run the 'wireviz pn.yaml' command
    try:
        subprocess.run(["wireviz", fileio.name("harness yaml")], check=True)
    except subprocess.CalledProcessError as e:
        print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Error while running wireviz: {e}")
        return

    def silentremove(filepath):
        if os.path.exists(filepath):
            os.remove(filepath)

    silentremove(fileio.path("wireviz bom"))
    silentremove(fileio.path("wireviz html"))
    silentremove(fileio.path("wireviz png"))
    silentremove(fileio.path("wireviz svg"))

    shutil.move(os.path.join(os.getcwd(),fileio.name("wireviz bom")),fileio.dirpath("wireviz_outputs"))
    shutil.move(os.path.join(os.getcwd(),fileio.name("wireviz html")),fileio.dirpath("wireviz_outputs"))
    shutil.move(os.path.join(os.getcwd(),fileio.name("wireviz png")),fileio.dirpath("wireviz_outputs"))
    shutil.move(os.path.join(os.getcwd(),fileio.name("wireviz svg")),fileio.dirpath("wireviz_outputs"))
    
    # Copy and format svg output as needed for later use
    shutil.copy(fileio.path("wireviz svg"), fileio.dirpath("svg_generated"))
    os.rename(os.path.join(fileio.dirpath("svg_generated"),fileio.name("wireviz svg")), fileio.path("esch master svg"))
    svg_utils.add_entire_svg_file_contents_to_group(fileio.path("esch master svg"), "esch-master")
