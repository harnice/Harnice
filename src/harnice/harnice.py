import run_wireviz
import wirelist
import instances_list
import svg_utils
import flagnote_functions
import formboard_functions
import harnice_prechecker
import component_library
import fileio
import svg_master_formboard
import svg_masters
import os
import svg_harnice_output

def harnice():
    #build file structure
    fileio.generate_structure()

    #check if revision history is set up correctly
    print()
    print("############ CHECKING REV HISTORY #############")
    if(harnice_prechecker.harnice_prechecker() == False):
        return

    #make a list of every single instance in the project
    print()
    print("############ GENERATING AN INSTANCES LIST #############")
    instances_list.make_new_list()
    instances_list.add_connectors()
    instances_list.add_cables()
    wirelist.newlist()

    print()
    print("############ CHECKING COMPONENTS AGAINST LIBRARY #############")
    component_library.pull_parts()
    
    print()
    print("############ RUNNING FORMBOARD PROCESSOR #############")
    print("Generating nodes from connectors")
    instances_list.generate_nodes_from_connectors()
    print()

    print("Pulling in preferred parent_csys and component offsets from component data")
    instances_list.update_parent_csys()
    instances_list.update_component_translate()
    print()

    if not os.path.exists(fileio.name("formboard graph definition")):
        print("Making a blank formboard definition file")
        with open(fileio.name("formboard graph definition"), 'w') as f:
            pass  # Creates an empty file
    else:
        print("Formboard definition file exists, preserving")
    print()

    print("Validating nodes exist and generating segments if they don't")
    formboard_functions.validate_nodes()
    print()

    print("Adding stuff from formboard processor into instances list")
    instances_list.add_nodes_from_formboard()
    instances_list.add_segments_from_formboard()
    print()

    print("Validating segments are structured correctly")
    formboard_functions.map_cables_to_segments()
    formboard_functions.detect_loops()
    formboard_functions.detect_dead_segments()
    print()

    print("Generating node and segment coordinates")
    formboard_functions.generate_node_coordinates()
    print()

    print("Adding lengths to instances list and wirelist")
    instances_list.add_cable_lengths()
    wirelist.add_lengths()
    print()

    print("Exporting a beautiful wirelist")
    wirelist.tsv_to_xls()
    print()

    print("Adding angles to nodes")
    instances_list.add_absolute_angles_to_segments()
    instances_list.add_angles_to_nodes()
    print()

    #condense instance list into a bom
    print()
    print("############ GENERATING A BOM #############")
    instances_list.convert_to_bom()
    instances_list.add_bom_line_numbers()

    #run wireviz
    print()
    print("############ RUNNING WIREVIZ #############")
    run_wireviz.generate_esch()

    #print()
    #print()
    #print("############ LOOKING FOR BUILDNOTES FILE #############")
    #flagnote_functions.look_for_buildnotes_file()

    print()
    print("############ REBUILDING FORMBOARD DRAWING #############")
    #generate blank harnice output svg
    print("Updating segment instances")
    svg_master_formboard.update_segment_instances()
    print()

    print("Generating new fomboard master drawing (deleting existing if present)")
    svg_master_formboard.make_new_formboard_master_svg()
    #formboard_illustration_functions.delete_unmatched_files()

    #prep all the different master SVG's
    print()
    print("############ REBUILDING HARNICE OUTPUT #############")
    print("Updating page setup")
    fileio.update_output_contents()
    print("Working on BOM svg master")
    svg_masters.prep_bom()
    print("Working on Harnice Output")
    svg_harnice_output.update_harnice_output()
    

    #combine all master SVG groups into PN-harnice-output.svg
    #print()
    #print("############ REGENERATE PN-HARNICE-OUTPUT.SVG #############")
    #rsvg_section_replacer.egen_harnice_output_svg()

    return

if __name__ == "__main__":
    harnice()