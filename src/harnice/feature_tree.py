import os
from harnice import fileio

def generate_default_feature_tree():
    """
    Creates a default, fully-expanded feature_tree.py in the current part's directory.
    """
    target_path = fileio.path("feature tree")
    os.makedirs(os.path.dirname(target_path), exist_ok=True)

    contents = '''\
from harnice import (
    fileio, instances_list, component_library, wirelist,
    svg_outputs, flagnotes, formboard, run_wireviz, rev_history, svg_utils
)
import os

#=============== INITIALIZE INSTANCES LIST #===============
#make a list of every single instance in the project

instances_list.make_new_list()
    #makes blank document
instances_list.add_connectors()
    #adds connectors from the yaml to that document
instances_list.add_cables()
    #adds cables from the yaml to that document
wirelist.newlist()
    #makes a new wirelist

#=============== CHECKING COMPONENTS AGAINST LIBRARY #===============
component_library.pull_parts()
    #compares existing imported library files against library
    #imports new files if they don't exist
    #if they do exist,
    #checks for updates against the library
    #checks for modifications against the library

#=============== PRODUCING A FORMBOARD BASED ON DEFINED ESCH #===============
instances_list.generate_nodes_from_connectors()
    #makes at least one node per connector, named the same as connectors for now

instances_list.update_parent_csys()
    #updates parent csys of each connector based on its definition json

instances_list.update_component_translate()
    #updates translations of any kind of instance with respect to its csys

#make a formboard definition file from scratch if it doesn't exist
if not os.path.exists(fileio.name("formboard graph definition")):
    with open(fileio.name("formboard graph definition"), 'w') as f:
        pass  # Creates an empty file

formboard.validate_nodes()
instances_list.add_nodes_from_formboard()
instances_list.add_segments_from_formboard()
    #validates all nodes exist
    #generates segments if they don't exist
    #adds nodes and segments into the instances list

print()
print("Validating your formboard graph is structured properly...")
formboard.map_cables_to_segments()
formboard.detect_loops()
formboard.detect_dead_segments()
    #validates segments are structured correctly

formboard.generate_node_coordinates()
    #starting from one node, recursively find lengths and angles of related segments to produce locations of each node

instances_list.add_cable_lengths()
wirelist.add_lengths()
    #add cable lengths to instances and wirelists

wirelist.tsv_to_xls()
    #now that wirelist is complete, make it pretty

instances_list.add_absolute_angles_to_segments()
    #add absolute angles to segments only such that they show up correctly on formboard
    #segments only, because every other instance angle is associated with its parent node
    #segments have by defintiion more than one node, so there's no easy way to resolve segment angle from that
instances_list.add_angles_to_nodes()
    #add angles to nodes to base the rotation of each node child instance

#=============== GENERATING A BOM #===============
instances_list.convert_to_bom()
    #condenses an instance list down into a bom
instances_list.add_bom_line_numbers()
    #adds bom line numbers back to the instances list

#=============== HANDLING FLAGNOTES #===============
#ensure page setup is defined, if not, make a basic one. flagnotes depends on this
page_setup_contents = svg_outputs.update_page_setup_json()

flagnotes.ensure_manual_list_exists()

#makes notes of part name, bom, revision, etc
flagnotes.compile_all_flagnotes()

#adds the above to instance list
instances_list.add_flagnotes()

flagnotes.make_note_drawings()
flagnotes.make_leader_drawings()

#=============== RUNNING WIREVIZ #===============
run_wireviz.generate_esch()

#=============== REBUILDING OUTPUT SVG #===============
revinfo = rev_history.revision_info()
rev_history.update_datemodified()

#add parent types to make filtering easier
instances_list.add_parent_instance_type()

#prepare the building blocks as svgs
svg_outputs.prep_formboard_drawings(page_setup_contents)
svg_outputs.prep_wirelist()
svg_outputs.prep_bom()
svg_outputs.prep_buildnotes_table()
svg_outputs.prep_revision_table()
#esch done under run_wireviz.generate_esch()

svg_outputs.prep_tblocks(page_setup_contents, revinfo)

svg_outputs.prep_master(page_setup_contents)
    #merges all building blocks into one main support_do_not_edit master svg file

svg_outputs.update_harnice_output(page_setup_contents)
    #adds the above to the user-editable svgs in page setup, one per page

svg_utils.produce_multipage_harnice_output_pdf(page_setup_contents)
    #makes a PDF out of each svg in page setup
'''

    with open(target_path, "w", encoding="utf-8") as f:
        f.write(contents)
    print(f"[INFO] Created default feature_tree.py at {target_path}")
