import os
import yaml
import re
from harnice import (
    fileio, instances_list, component_library, wirelist,
    svg_outputs, flagnotes, formboard, run_wireviz, rev_history, svg_utils,
    harness_yaml
)

"""
Terminology:
- A "circuit" is a logical group of ports that are electrically connected.
- A "port" is a named electrical interface, such as a pin, terminal, or wire end.
- The "nets" connecting ports are implied by being in the same circuit; they are not explicitly listed.
"""

#=============== INITIALIZE INSTANCES LIST #===============
# make a list of every single instance in the project

instances_list.make_new_list()
    # makes blank document

#=============== GENERATE INSTANCES FROM ESCH #===============
"""
Expected YAML example:
-----------------------
circuit1:
    portA:
    cavity: 7
    contact: testpoint
    portB:
    conductor: 1

From this input, the following instance names will be generated and written:
- portA
- portA.cavity7
- circuit1.contact1         (contact items are numbered within the circuit)
- portB
- portB.conductor1

Each instance is written immediately to the instance list if not already present.
"""
harness_yaml = harness_yaml.load()

# For each electrical circuit (or net) in your system
# Circuit name is a string, ports is a dictionary that contains all the stuff on that circuit
for circuit_name, ports in harness_yaml.items():
    contact_counter = 1  # This helps automatically number contact points like contact1, contact2, etc.

    # Go through each port in this circuit
    # Port label is the port, value is either a string or a dictionary
    for port_label, value in ports.items():

        if port_label == "contact":
            # Automatically name the contact with the circuit name and a number
            instance_name = f"{circuit_name}.contact{contact_counter}"
            contact_counter += 1

            # Add this contact to the system with its part number (mpn)
            instances_list.add_instance_unless_exists({
                "instance_name": instance_name,
                "item_type": "Contact",  # This tells the software what kind of part this is
                "mpn": value,
                "parent_instance": port_label
            })

        else:
            # Check the label of the port to decide what kind of part it is.
            # By default, anything starting with "X" or "W" is treated as a Connector.
            if re.match(r"X[^.]+", port_label):
                item_type = "Connector"
            elif re.match(r"W[^.]+", port_label):
                item_type = "Connector"
            else:
                item_type = ""  # If we don't know what this is, leave it blank.

            # Add the connector (or unknown type) to the system
            instances_list.add_instance_unless_exists({
                "instance_name": port_label,
                "item_type": item_type
            })

            # If the port contains more detailed information (like cavity or conductor),
            # the value will be a dictionary with extra fields
            if type(value) is dict:
                for subkey, subval in value.items():

                    # If the field is "cavity", add a cavity under this connector
                    if subkey == "cavity":
                        instance_name = f"{port_label}.cavity{subval}"
                        instances_list.add_instance_unless_exists({
                            "instance_name": instance_name,
                            "item_type": "Connector cavity",
                            "mpn": "N/A",  # Not applicable here, so we fill in "N/A"
                            "parent_instance": port_label
                        })

                    # If the field is "conductor", add a conductor under this wire
                    elif subkey == "conductor":
                        instance_name = f"{port_label}.conductor{subval}"
                        instances_list.add_instance_unless_exists({
                            "instance_name": instance_name,
                            "item_type": "Conductor",
                            "mpn": "N/A",
                            "parent_instance": port_label
                        })

                    # If the field is something else (like "shield" or "tag"), we still include it
                    else:
                        instance_name = f"{port_label}.{subkey}{subval}"
                        instances_list.add_instance_unless_exists({
                            "instance_name": instance_name
                        })

            else:
                # If the port is just a single value (not a dictionary), we still add it as a sub-instance
                instance_name = f"{port_label}.{value}"
                instances_list.add_instance_unless_exists({
                    "instance_name": instance_name
                })

instances_list.add_connectors()
    # adds connectors from the yaml to that document
instances_list.add_cables()
    # adds cables from the yaml to that document
wirelist.newlist()
    # makes a new wirelist

#=============== CHECKING COMPONENTS AGAINST LIBRARY #===============
component_library.pull_parts()
    # compares existing imported library files against library
    # imports new files if they don't exist
    # if they do exist,
    # checks for updates against the library
    # checks for modifications against the library

#=============== PRODUCING A FORMBOARD BASED ON DEFINED ESCH #===============
instances_list.generate_nodes_from_connectors()
    # makes at least one node per connector, named the same as connectors for now

instances_list.update_parent_csys()
    # updates parent csys of each connector based on its definition json

instances_list.update_component_translate()
    # updates translations of any kind of instance with respect to its csys

# make a formboard definition file from scratch if it doesn't exist
if not os.path.exists(fileio.name("formboard graph definition")):
    with open(fileio.name("formboard graph definition"), 'w') as f:
        pass  # Creates an empty file

exit()
formboard.validate_nodes()
instances_list.add_nodes_from_formboard()
instances_list.add_segments_from_formboard()
    # validates all nodes exist
    # generates segments if they don't exist
    # adds nodes and segments into the instances list

print()
print("Validating your formboard graph is structured properly...")
formboard.map_cables_to_segments()
formboard.detect_loops()
formboard.detect_dead_segments()
    # validates segments are structured correctly

formboard.generate_node_coordinates()
    # starting from one node, recursively find lengths and angles of related segments to produce locations of each node

instances_list.add_cable_lengths()
wirelist.add_lengths()
    # add cable lengths to instances and wirelists

wirelist.tsv_to_xls()
    # now that wirelist is complete, make it pretty

instances_list.add_absolute_angles_to_segments()
    # add absolute angles to segments only such that they show up correctly on formboard
    # segments only, because every other instance angle is associated with its parent node
    # segments have by defintiion more than one node, so there's no easy way to resolve segment angle from that
instances_list.add_angles_to_nodes()
    # add angles to nodes to base the rotation of each node child instance

#=============== GENERATING A BOM #===============
instances_list.convert_to_bom()
    # condenses an instance list down into a bom
instances_list.add_bom_line_numbers()
    # adds bom line numbers back to the instances list

#=============== HANDLING FLAGNOTES #===============
# ensure page setup is defined, if not, make a basic one. flagnotes depends on this
page_setup_contents = svg_outputs.update_page_setup_json()

flagnotes.ensure_manual_list_exists()

# makes notes of part name, bom, revision, etc
flagnotes.compile_all_flagnotes()

# adds the above to instance list
instances_list.add_flagnotes()

flagnotes.make_note_drawings()
flagnotes.make_leader_drawings()

#=============== RUNNING WIREVIZ #===============
run_wireviz.generate_esch()

#=============== REBUILDING OUTPUT SVG #===============
revinfo = rev_history.revision_info()
rev_history.update_datemodified()

# add parent types to make filtering easier
instances_list.add_parent_instance_type()

# prepare the building blocks as svgs
svg_outputs.prep_formboard_drawings(page_setup_contents)
svg_outputs.prep_wirelist()
svg_outputs.prep_bom()
svg_outputs.prep_buildnotes_table()
svg_outputs.prep_revision_table()
# esch done under run_wireviz.generate_esch()

svg_outputs.prep_tblocks(page_setup_contents, revinfo)

svg_outputs.prep_master(page_setup_contents)
    # merges all building blocks into one main support_do_not_edit master svg file

svg_outputs.update_harnice_output(page_setup_contents)
    # adds the above to the user-editable svgs in page setup, one per page

svg_utils.produce_multipage_harnice_output_pdf(page_setup_contents)
    # makes a PDF out of each svg in page setup
