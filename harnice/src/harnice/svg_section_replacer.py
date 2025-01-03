import os
from os.path import basename
from inspect import currentframe
from utility import partnumber, find_and_replace_svg_group


def regen_harnice_output_svg():

    # Perform the find-and-replace operations using the dynamically generated filenames
    find_and_replace_svg_group(os.path.join(os.getcwd(), f"{partnumber("pn-rev")}-harnice-output.svg"), os.path.join(os.getcwd(), "support-do-not-edit", "master-svgs", f"{partnumber("pn-rev")}-formboard-master.svg"), "formboard-master")
    print()
    find_and_replace_svg_group(os.path.join(os.getcwd(), f"{partnumber("pn-rev")}-harnice-output.svg"), os.path.join(os.getcwd(), "support-do-not-edit", "master-svgs", f"{partnumber("pn-rev")}-bom-table-master.svg"), "bom-master")
    print()
    find_and_replace_svg_group(os.path.join(os.getcwd(), f"{partnumber("pn-rev")}-harnice-output.svg"), os.path.join(os.getcwd(), "support-do-not-edit", "master-svgs", f"{partnumber("pn-rev")}-revision-history-master.svg"), "revision-history-master")
    print()
    find_and_replace_svg_group(os.path.join(os.getcwd(), f"{partnumber("pn-rev")}-harnice-output.svg"), os.path.join(os.getcwd(), "support-do-not-edit", "master-svgs", f"{partnumber("pn-rev")}-tblock-master.svg"), "tblock-master")
    print()
    find_and_replace_svg_group(os.path.join(os.getcwd(), f"{partnumber("pn-rev")}-harnice-output.svg"), os.path.join(os.getcwd(), "support-do-not-edit", "master-svgs", f"{partnumber("pn-rev")}-buildnotes-master.svg"), "buildnotes-master")
    print()
    find_and_replace_svg_group(os.path.join(os.getcwd(), f"{partnumber("pn-rev")}-harnice-output.svg"), os.path.join(os.getcwd(), "support-do-not-edit", "master-svgs", f"{partnumber("pn-rev")}-esch-master.svg"), "esch-master")
    print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: No more replacements.")

if __name__ == "__main__":
    regen_harnice_output_svg()