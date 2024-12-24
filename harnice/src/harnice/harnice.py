from run_wireviz import generate_esch
from bom_concatenator import combine_tsv_boms
from esch_to_wirelist import esch_to_wirelist
from generate_connector_list import generate_connector_list
from svg_section_replacer import regen_harnice_output_svg
from generate_blank_svg import generate_blank_svg
from bom_svg_prepper import prep_bom_svg_master
from tblock_svg_prepper import prep_tblock_svg_master
from formboard_functions import formboard_processor
from flagnote_functions import look_for_buildnotes_file
from harnice_prechecker import harnice_prechecker
from utility import file_exists_in_directory, pn_from_dir
from formboard_illustration_functions import regen_formboard
import os

def harnice():
    #check if revision history is set up correctly
    print()
    print("############ CHECKING REV HISTORY #############")
    if(harnice_prechecker() == False):
        return

    #run wireviz
    print()
    print("############ RUNNING WIREVIZ #############")
    generate_esch()

    #generating a wirelist
    print()
    print("############ GENERATING A NO-LENGTHS WIRELIST #############")
    esch_to_wirelist()

    #generating a connector list
    print()
    print("############ GENERATING A CONNECTORS LIST #############")
    generate_connector_list()

    print()
    print("############ LOOKING FOR BUILDNOTES FILE #############")
    look_for_buildnotes_file()

    #rerun formboard processor
    print()
    print("############ RUNNING FORMBOARD PROCESSOR #############")
    formboard_processor()

    #combine elec, mech, wire boms into pn-harness-bom
    print()
    print("############ COMBINING BOMS #############")
    combine_tsv_boms()

    #generate blank harnice output svg
    print()
    print("############ GENERATING BLANK HARNICE-OUTPUT.SVG #############")
    if not file_exists_in_directory(f"{pn_from_dir()}-harnice-output.svg"):
        print()
        generate_blank_svg()
    else :
        print(f"{pn_from_dir()}-harnice-output.svg already exists. To rebuild, delete this file and rerun. Moving on...")

    #prep all the different master SVG's
    print()
    print("############ PREPPING MASTER SVG's #############")
    prep_bom_svg_master()
    prep_tblock_svg_master()

    print()
    print("############ REBUILDING FORMBOARD DRAWING #############")
    regen_formboard()

    #combine all master SVG groups into PN-harnice-output.svg
    print()
    print("############ REGENERATE PN-HARNICE-OUTPUT.SVG #############")
    regen_harnice_output_svg()

    return

if __name__ == "__main__":
    harnice()