import run_wireviz
import bom_handler
import wirelist
import instances_list
import svg_section_replacer
import generate_harnice_output_svg
import bom_svg_prepper
import tblock_svg_prepper
import formboard_functions
import flagnote_functions
import harnice_prechecker
import fileio
import formboard_illustration_functions
import os

def harnice():
    #build file structure
    fileio.generate_structure()

    #check if revision history is set up correctly
    print()
    print("############ CHECKING REV HISTORY #############")
    if(harnice_prechecker.harnice_prechecker() == False):
        return

    #generating a connector list
    print()
    print("############ GENERATING AN INSTANCES LIST #############")
    instances_list.make_new_list()
    instances_list.add_connectors()
    instances_list.add_cables()
    wirelist.newlist()

    #run formboard processor
    print()
    print("############ RUNNING FORMBOARD PROCESSOR #############")
    #update this function to account for new instances list formatting:
    formboard_functions.formboard_processor()
    instances_list.add_formboard_segments()
    instances_list.add_cable_lengths()

    #run wireviz
    print()
    print("############ RUNNING WIREVIZ #############")
    run_wireviz.generate_esch()

    #print()
    print("############ LOOKING FOR BUILDNOTES FILE #############")
    flagnote_functions.look_for_buildnotes_file()

    #combine elec, mech, wire boms into pn-harness-bom
    #print()
    #print("############ COMBINING BOMS #############")
    #bom_handler.process_boms()

    #prep all the different master SVG's
    #print()
    #print("############ PREPPING MASTER SVG's #############")
    #print("#    ############ WORKING ON BOM SVG MASTER ############")
    #bom_svg_prepper.prep_bom_svg_master()
    #print("#    ############ WORKING ON TBLOCK SVG MASTER ############")
    #tblock_svg_prepper.prep_tblock_svg_master()

    #print()
    #print("############ REBUILDING FORMBOARD DRAWING #############")
    #formboard_illustration_functions.regen_formboard()

    #generate blank harnice output svg
    #print()
    #print("############ GENERATING BLANK HARNICE-OUTPUT.SVG #############")
    #if not utility.file_exists_in_directory(f"{fileio.partnumber("pn-rev")}-harnice-output.svg"):
    #TODO: file_exists_in_directory(search_for_filename, directory=".") should be changed to os.path.isfile(os.path.join(directory, search_for_filename))
        #print()
        #generate_harnice_output_svg.generate_blank_harnice_output_svg()
    #else :
        #print(f"{fileio.partnumber("pn-rev")}-harnice-output.svg already exists")
        #generate_harnice_output_svg.ensure_groups_exist_in_harnice_output()

    #combine all master SVG groups into PN-harnice-output.svg
    #print()
    #print("############ REGENERATE PN-HARNICE-OUTPUT.SVG #############")
    #rsvg_section_replacer.egen_harnice_output_svg()

    return

if __name__ == "__main__":
    harnice()