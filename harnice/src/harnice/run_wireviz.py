import os
import time
import subprocess
import shutil
from os.path import basename
from inspect import currentframe
from utility import *

def generate_esch():
    # Run the 'wireviz pn.yaml' command
    try:
        subprocess.run(["wireviz", filename("wireviz yaml")], check=True)
    except subprocess.CalledProcessError as e:
        print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Error while running wireviz: {e}")
        return
    
    # Rename, create directory if not existent, and move the SVG file
    wireviz_svg_filename = f"{partnumber("pn-rev")}.svg"
    rename_file(wireviz_svg_filename, filename("esch master svg"), True)
    os.makedirs(dirpath("master_svgs"), exist_ok=True)
    shutil.move(os.path.join(os.getcwd(), filename("esch master svg")), filepath("esch master svg"))
    
    # Modify the SVG file
    add_entire_svg_file_contents_to_group(filepath("esch master svg"), "esch-master")

    # Rename, create directory if not existent, and move the bom file
    rename_file(f"{partnumber("pn-rev")}.bom.tsv", filename("electrical bom"), True)
    os.makedirs(dirpath("boms"), exist_ok=True)
    shutil.move(os.path.join(os.getcwd(), filename("electrical bom")), filepath("electrical bom"))

    # Delete the HTML file
    html_filename = f"{partnumber("pn-rev")}.html"
    if os.path.exists(html_filename):
        try:
            os.remove(html_filename)
            print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Deleted file: {html_filename}")
        except OSError as e:
            print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Error deleting file {html_filename}: {e}")
    else:
        print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: File {html_filename} does not exist.")


# Run the process
if __name__ == "__main__":
    run_wireviz()
