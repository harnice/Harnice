import os
import time
import subprocess
import shutil
from os.path import basename
from inspect import currentframe
from utility import *

def generate_esch():
    #duplicate yaml and move to wireviz folder
    shutil.copy(filepath("harness yaml"), dirpath("wireviz"))
    original_working_directory = os.getcwd()
    os.chdir(dirpath("wireviz"))

    # Run the 'wireviz pn.yaml' command
    try:
        subprocess.run(["wireviz", filename("harness yaml")], check=True)
    except subprocess.CalledProcessError as e:
        print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Error while running wireviz: {e}")
        return
    
    # Rename, create directory if not existent, and move the SVG file
    wireviz_svg_filename = f"{partnumber("pn-rev")}.svg"
    rename_file(wireviz_svg_filename, filename("esch master svg"), True)
    shutil.move(os.path.join(os.getcwd(), filename("esch master svg")), filepath("esch master svg"))
    
    # Modify the SVG file
    add_entire_svg_file_contents_to_group(filepath("esch master svg"), "esch-master")

    os.chdir(original_working_directory)

# Run the process
if __name__ == "__main__":
    run_wireviz()
