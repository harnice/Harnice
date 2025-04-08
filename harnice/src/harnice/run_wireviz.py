import os
import time
import subprocess
import shutil
import svg_utils
from os.path import basename
from inspect import currentframe
import fileio

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
    shutil.copy(fileio.path("wireviz svg"), fileio.dirpath("master_svgs"))
    os.rename(os.path.join(fileio.dirpath("master_svgs"),fileio.name("wireviz svg")), fileio.path("esch master svg"))
    svg_utils.add_entire_svg_file_contents_to_group(fileio.path("esch master svg"), "esch-master")

# Run the process
if __name__ == "__main__":
    run_wireviz()
