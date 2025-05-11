import run_wireviz
import wirelist
import instances_list
import svg_utils
import flagnote_functions
import formboard_functions
import harnice_prechecker
import component_library
import fileio
import svg_blocks
import svg_generated
import svg_harnice_output
import os

def harnice():
    #check if revision history is set up correctly
    print()
    print("############ CHECKING REV HISTORY #############")
    if(harnice_prechecker.harnice_prechecker() == False):
        return
    
    #build file structure
    fileio.generate_structure()

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
    print("############ REBUILDING SVGs #############")
    #===================================
    #FIRST COMPLETE GENERATED SVGS
    svg_generated.make_new_formboard_master_svg()
    svg_generated.prep_wirelist()
    #TODO: revision history
    #TODO: buildnotes table
    svg_generated.prep_bom()
    #esch done under run_wireviz.generate_esch()


    #===================================
    #NEXT COMPLETE BLOCKS (direct compilations and library imports of the above)
    svg_blocks = fileio.update_page_setup_json()

    #titleblocks
    for tblock_name, tblock_entry in svg_blocks.get("titleblocks", {}).items():
        #update that instance
        print(f"!!!!!!!! {tblock_name}")
        #svg_utils.update_svg_instance(svg_instance)

    #formboards
    for formboard_name, formboard_entry in svg_blocks.get("formboards", {}).items():
        #update that instance
        print(f"!!!!!!!! {formboard_name}")
        #svg_utils.update_svg_instance(svg_instance)

    
    #===================================
    #LAST, MERGE THEM ALL INTO A USEFUL OUTPUT FILE
    #merge them all into one parent support_do_not_edit file
    svg_harnice_output.update_support_do_not_edit_group()

    #add the above to the user-editable main output svg
    svg_harnice_output.update_harnice_output()
    

if __name__ == "__main__":
    harnice()