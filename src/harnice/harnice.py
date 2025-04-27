import run_wireviz
import wirelist
import instances_list
import svg_utils
import formboard_functions
import flagnote_functions
import formboard_functions_new
import harnice_prechecker
import component_library
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

    #make a list of every single instance in the project
    print()
    print("############ GENERATING AN INSTANCES LIST #############")
    instances_list.make_new_list()
    instances_list.add_connectors()
    instances_list.add_cables()
    wirelist.newlist()

    print()
    print("############ CHECKING COMPONENTS AGAINST LIBRARY #############")
    component_library.pull()
    
    #process the formboard definition to get the list of segments and their locations
    print()
    print("############ RUNNING FORMBOARD PROCESSOR #############")
    print("Generating nodes from connectors")
    formboard_functions_new.generate_nodes_from_connectors()
    print()

    if not(formboard definition exists) == True:
        print("Making a blank formboard definition file")
        mkdir
    else:
        print("Formboard definition file exists, preserving")
    print()

    print("Validating nodes agree with segments agree with yaml")
    formboard_functions_new.validate_nodes()
    print()

    print("Validating segments are structured correctly and map to wires")
    formboard_functions_new.validate_segments()
    print()

    print("Generating node locations")
    formboard_functions_new.generate_node_locations()
    
    """
    print("Running formboard_functions.formboard_processor()")
    formboard_functions.formboard_processor()
    print("Segments and nodes exist only within their source of truth which is 'formboard graph definition'")
    print()

    print("Running instances_list.add_nodes()")
    instances_list.add_nodes()
    print("Nodes now exist in instances list but do not have any attributes yet")
    print()

    print("Running instances_list.add_formboard_segments()")
    instances_list.add_formboard_segments()
    print("Segments now exist in instances list with attributes length and diameter as defined in 'formboard graph definition")
    print()
    exit()

    formboard_functions.map_connections_to_graph()
    instances_list.add_cable_lengths()
    #segments now exist in instances list but do not have attributes
    wirelist.add_lengths()
    #wirelist now contains wirelengths
    wirelist.tsv_to_xls()
    formboard_functions.generate_node_coordinates()
    formboard_functions.visualize_formboard_graph()
    """
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
    instances_list.update_parent_csys()
    instances_list.update_component_translate()
    formboard_illustration_functions.update_all_instances()
    #formboard_illustration_functions.update_segment_instances()
    #formboard_illustration_functions.delete_unmatched_files()
    #formboard_illustration_functions.update_formboard_master_svg()
    #formboard_illustration_functions.replace_all_segment_groups()

    #prep all the different master SVG's
    #print()
    #print("############ PREPPING MASTER SVG's #############")
    #print("#    ############ WORKING ON BOM SVG MASTER ############")
    #bom_svg_prepper.prep_bom_svg_master()
    #print("#    ############ WORKING ON TBLOCK SVG MASTER ############")
    #tblock_svg_prepper.prep_tblock_svg_master()
    
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