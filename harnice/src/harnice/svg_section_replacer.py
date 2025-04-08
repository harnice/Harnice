import os
from os.path import basename
from inspect import currentframe
import fileio
import svg_utils

def regen_harnice_output_svg():

    # Perform the find-and-replace operations using the dynamically generated filenames
    svg_utils.find_and_replace_svg_group(fileio.path("harnice output"), fileio.path("formboard master svg"), "formboard-master")
    print()
    svg_utils.find_and_replace_svg_group(fileio.path("harnice output"), fileio.path("bom table master svg"), "bom-master")
    print()
    svg_utils.find_and_replace_svg_group(fileio.path("harnice output"), fileio.path("revhistory master svg"), "revision-history-master")
    print()
    svg_utils.find_and_replace_svg_group(fileio.path("harnice output"), fileio.path("tblock master svg"), "tblock-master")
    print()
    svg_utils.find_and_replace_svg_group(fileio.path("harnice output"), fileio.path("buildnotes master svg"), "buildnotes-master")
    print()
    svg_utils.find_and_replace_svg_group(fileio.path("harnice output"), fileio.path("esch master svg"), "esch-master")
    print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: No more replacements.")

if __name__ == "__main__":
    regen_harnice_output_svg()