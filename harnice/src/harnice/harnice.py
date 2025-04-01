from run_wireviz import generate_esch
from bom_handler import process_boms
from esch_to_wirelist import esch_to_wirelist, wirelist_add_lengths
from generate_instances_list import generate_instances_list
from svg_section_replacer import regen_harnice_output_svg
from generate_harnice_output_svg import generate_blank_harnice_output_svg, ensure_groups_exist_in_harnice_output
from bom_svg_prepper import prep_bom_svg_master
from tblock_svg_prepper import prep_tblock_svg_master
from formboard_functions import formboard_processor
from flagnote_functions import look_for_buildnotes_file
from harnice_prechecker import harnice_prechecker
from utility import *
from formboard_illustration_functions import regen_formboard
import os

def harnice():
    #build file structure
    generate_file_structure()

    #check if revision history is set up correctly
    print()
    print("############ CHECKING REV HISTORY #############")
    if(harnice_prechecker() == False):
        return

    #run wireviz
    #temporarily turning these off in issue-13 to decouple them from instance list
    #print()
    #print("############ RUNNING WIREVIZ #############")
    #generate_esch()

    #generating a wirelist
    #temporarily turning these off in issue-13 to decouple them from instance list
    #print()
    #print("############ GENERATING A NO-LENGTHS WIRELIST #############")
    #esch_to_wirelist()

    #generating a connector list
    print()
    print("############ GENERATING AN INSTANCES LIST #############")
    generate_instances_list()

    print()
    print("############ LOOKING FOR BUILDNOTES FILE #############")
    look_for_buildnotes_file()

    exit()

    #rerun formboard processor
    print()
    print("############ RUNNING FORMBOARD PROCESSOR #############")
    formboard_processor()
    #wirelist_add_lengths()

    #combine elec, mech, wire boms into pn-harness-bom
    print()
    print("############ COMBINING BOMS #############")
    process_boms()

    #prep all the different master SVG's
    print()
    print("############ PREPPING MASTER SVG's #############")
    print("#    ############ WORKING ON BOM SVG MASTER ############")
    prep_bom_svg_master()
    print("#    ############ WORKING ON TBLOCK SVG MASTER ############")
    prep_tblock_svg_master()

    print()
    print("############ REBUILDING FORMBOARD DRAWING #############")
    regen_formboard()

    #generate blank harnice output svg
    print()
    print("############ GENERATING BLANK HARNICE-OUTPUT.SVG #############")
    if not file_exists_in_directory(f"{partnumber("pn-rev")}-harnice-output.svg"):
        print()
        generate_blank_harnice_output_svg()
    else :
        print(f"{partnumber("pn-rev")}-harnice-output.svg already exists")
        ensure_groups_exist_in_harnice_output()

    #combine all master SVG groups into PN-harnice-output.svg
    print()
    print("############ REGENERATE PN-HARNICE-OUTPUT.SVG #############")
    regen_harnice_output_svg()

    return

if __name__ == "__main__":
    harnice()