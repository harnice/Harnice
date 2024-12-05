import os
import time
import subprocess
import shutil
from os.path import basename
from inspect import currentframe
from utility import pn_from_dir, add_entire_svg_file_contents_to_group, rename_file, delete_file

def generate_esch():
    # Construct the YAML, SVG, and HTML file names
    yaml_filename = f"{pn_from_dir()}.yaml"
    wireviz_svg_filename = f"{pn_from_dir()}.svg"
    harnice_svg_filename = f"{pn_from_dir()}-esch-master.svg"
    html_filename = f"{pn_from_dir()}.html"

    # Run the 'wireviz pn.yaml' command
    try:
        subprocess.run(["wireviz", yaml_filename], check=True)
    except subprocess.CalledProcessError as e:
        print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Error while running wireviz: {e}")
        return
    
    # Rename, create directory if not existent, and move the SVG file
    rename_file(wireviz_svg_filename, harnice_svg_filename, True)
    os.makedirs(os.path.join(os.getcwd(), "support-do-not-edit", "master-svgs"), exist_ok=True)
    shutil.move(os.path.join(os.getcwd(), harnice_svg_filename), os.path.join(os.path.join(os.getcwd(), "support-do-not-edit", "master-svgs"), harnice_svg_filename))
    
    # Modify the SVG file
    add_entire_svg_file_contents_to_group(os.path.join(os.getcwd(), "support-do-not-edit", "master-svgs", harnice_svg_filename), "esch-master")

    # Rename, create directory if not existent, and move the bom file
    new_bom_filename = f"{pn_from_dir()}-esch-electrical-bom.tsv"
    rename_file(f"{pn_from_dir()}.bom.tsv", new_bom_filename, True)
    os.makedirs(os.path.join(os.getcwd(), "support-do-not-edit", "boms"), exist_ok=True)
    shutil.move(os.path.join(os.getcwd(), new_bom_filename), os.path.join(os.path.join(os.getcwd(), "support-do-not-edit", "boms"), new_bom_filename))

    # Delete the HTML file
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
