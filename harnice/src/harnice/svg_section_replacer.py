import os
from os.path import basename
from inspect import currentframe
from utility import pn_from_dir, find_and_replace_svg_group


def regen_harnice_output_svg():
    # Get the project name from the directory
    pn = pn_from_dir()

    # Perform the find-and-replace operations using the dynamically generated filenames
    find_and_replace_svg_group(os.path.join(os.getcwd(), f"{pn}-harnice-output.svg"), os.path.join(os.getcwd(), "support-do-not-edit", "master-svgs", f"{pn}-formboard-master.svg"), "formboard-master")
    print()
    find_and_replace_svg_group(os.path.join(os.getcwd(), f"{pn}-harnice-output.svg"), os.path.join(os.getcwd(), "support-do-not-edit", "master-svgs", f"{pn}-bom-table-master.svg"), "bom-master")
    print()
    find_and_replace_svg_group(os.path.join(os.getcwd(), f"{pn}-harnice-output.svg"), os.path.join(os.getcwd(), "support-do-not-edit", "master-svgs", f"{pn}-revision-history-master.svg"), "revision-history-master")
    print()
    find_and_replace_svg_group(os.path.join(os.getcwd(), f"{pn}-harnice-output.svg"), os.path.join(os.getcwd(), "support-do-not-edit", "master-svgs", f"{pn}-tblock-master.svg"), "tblock-master")
    print()
    find_and_replace_svg_group(os.path.join(os.getcwd(), f"{pn}-harnice-output.svg"), os.path.join(os.getcwd(), "support-do-not-edit", "master-svgs", f"{pn}-buildnotes-master.svg"), "buildnotes-master")
    print()
    find_and_replace_svg_group(os.path.join(os.getcwd(), f"{pn}-harnice-output.svg"), os.path.join(os.getcwd(), "support-do-not-edit", "master-svgs", f"{pn}-esch-master.svg"), "esch-master")
    print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: No more replacements.")

if __name__ == "__main__":
    regen_harnice_output_svg()