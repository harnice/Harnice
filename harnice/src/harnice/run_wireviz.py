import os
import time
import subprocess
import shutil
from os.path import basename
from inspect import currentframe

import file

def generate_esch():
    # Run the 'wireviz pn.yaml' command
    try:
        subprocess.run(["wireviz", filename("harness yaml")], check=True)
    except subprocess.CalledProcessError as e:
        print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Error while running wireviz: {e}")
        return

    def silentremove(filepath):
        if os.path.exists(filepath):
            os.remove(filepath)

    silentremove(file.path("wireviz bom"))
    silentremove(file.path("wireviz html"))
    silentremove(file.path("wireviz png"))
    silentremove(file.path("wireviz svg"))

    shutil.move(os.path.join(os.getcwd(),filename("wireviz bom")),file.dirpath("wireviz_outputs"))
    shutil.move(os.path.join(os.getcwd(),filename("wireviz html")),file.dirpath("wireviz_outputs"))
    shutil.move(os.path.join(os.getcwd(),filename("wireviz png")),file.dirpath("wireviz_outputs"))
    shutil.move(os.path.join(os.getcwd(),filename("wireviz svg")),file.dirpath("wireviz_outputs"))
    
    # Copy and format svg output as needed for later use
    shutil.copy(file.path("wireviz svg"), file.dirpath("master_svgs"))
    os.rename(os.path.join(file.dirpath("master_svgs"),filename("wireviz svg")), file.path("esch master svg"))
    svg_utils.add_entire_svg_file_contents_to_group(file.path("esch master svg"), "esch-master")

# Run the process
if __name__ == "__main__":
    run_wireviz()
