import os
from os.path import basename
from inspect import currentframe

import file


def regen_harnice_output_svg():

    # Perform the find-and-replace operations using the dynamically generated filenames
    svg_utils.find_and_replace_svg_group(file.path("harnice output"), file.path("formboard master svg"), "formboard-master")
    print()
    svg_utils.find_and_replace_svg_group(file.path("harnice output"), file.path("bom table master svg"), "bom-master")
    print()
    svg_utils.find_and_replace_svg_group(file.path("harnice output"), file.path("revhistory master svg"), "revision-history-master")
    print()
    svg_utils.find_and_replace_svg_group(file.path("harnice output"), file.path("tblock master svg"), "tblock-master")
    print()
    svg_utils.find_and_replace_svg_group(file.path("harnice output"), file.path("buildnotes master svg"), "buildnotes-master")
    print()
    svg_utils.find_and_replace_svg_group(file.path("harnice output"), file.path("esch master svg"), "esch-master")
    print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: No more replacements.")

if __name__ == "__main__":
    regen_harnice_output_svg()