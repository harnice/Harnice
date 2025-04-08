import os
import time
import subprocess
import shutil
from os.path import basename
from inspect import currentframe
import utils
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

    silentremove(filepath("wireviz bom"))
    silentremove(filepath("wireviz html"))
    silentremove(filepath("wireviz png"))
    silentremove(filepath("wireviz svg"))

    shutil.move(os.path.join(os.getcwd(),filename("wireviz bom")),dirpath("wireviz_outputs"))
    shutil.move(os.path.join(os.getcwd(),filename("wireviz html")),dirpath("wireviz_outputs"))
    shutil.move(os.path.join(os.getcwd(),filename("wireviz png")),dirpath("wireviz_outputs"))
    shutil.move(os.path.join(os.getcwd(),filename("wireviz svg")),dirpath("wireviz_outputs"))
    
    # Copy and format svg output as needed for later use
    shutil.copy(filepath("wireviz svg"), dirpath("master_svgs"))
    os.rename(os.path.join(dirpath("master_svgs"),filename("wireviz svg")), filepath("esch master svg"))
    add_entire_svg_file_contents_to_group(filepath("esch master svg"), "esch-master")

# Run the process
if __name__ == "__main__":
    run_wireviz()
