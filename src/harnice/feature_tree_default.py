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
# For each electrical circuit (or net) in your system
# Circuit name is a string, ports is a dictionary that contains all the stuff on that circuit
for circuit_name, ports in harness_yaml.load().items():
    port_counter = 0
    contact_counter = 0  # This helps automatically number contact points like contact1, contact2, etc.

    # Go through each port in this circuit
    # Port label is the port, value is either a string or a dictionary
    for port_label, value in ports.items():

        if port_label == "contact":
            # Automatically name the contact with the circuit name and a number
            instance_name = f"{circuit_name}.contact{contact_counter}"
            contact_counter += 1

            # Add this contact to the system with its part number (mpn)

            if value == "TXPA20":
                supplier = "public"

            instances_list.add_unless_exists(instance_name, {
                "item_type": "Contact",  # This tells the software what kind of part this is
                "mpn": value,
                "supplier": supplier,
                "location_is_node_or_segment": "Node",
                'circuit_id': circuit_name,
                'circuit_id_port': port_counter
            })

        else:
            # Check the label of the port to decide what kind of part it is.
            # By default, anything starting with "X" or "W" is treated as a Connector.
            if re.match(r"X[^.]+", port_label):
                instances_list.add_unless_exists(port_label,{
                    "item_type": "Connector",
                    "parent_instance": f"{port_label}.node",
                    "location_is_node_or_segment": "Node",
                })
                instances_list.add_unless_exists(f"{port_label}.node",{
                    "item_type": "Node",
                    "location_is_node_or_segment": "Node",
                    "mpn": "N/A"
                })
            elif re.match(r"C[^.]+", port_label):
                instances_list.add_unless_exists(port_label,{
                    "item_type": "Cable",
                    "parent_instance": port_label,
                    "location_is_node_or_segment": "Segment",
                })
            else:
                raise ValueError(f"Please define item {port_label}!")

            # If the port contains more detailed information (like cavity or conductor),
            # the value will be a dictionary with extra fields
            if type(value) is dict:
                for subkey, subval in value.items():

                    # If the field is "cavity", add a cavity under this connector
                    if subkey == "cavity":
                        instance_name = f"{port_label}.cavity{subval}"
                        instances_list.add_unless_exists(instance_name,{
                            "item_type": "Connector cavity",
                            "mpn": "N/A",  # Not applicable here, so we fill in "N/A"
                            "parent_instance": port_label,
                            "location_is_node_or_segment": "Node",
                            'circuit_id': circuit_name,
                            'circuit_id_port': port_counter
                        })

                    # If the field is "conductor", add a conductor under this wire
                    elif subkey == "conductor":
                        instance_name = f"{port_label}.conductor{subval}"
                        instances_list.add_unless_exists(instance_name,{
                            "item_type": "Conductor",
                            "mpn": "N/A",
                            "parent_instance": port_label,
                            "location_is_node_or_segment": "Segment",
                            'circuit_id': circuit_name,
                            'circuit_id_port': port_counter
                        })

                    # If the field is something else (like "shield" or "tag"), we still include it
                    else:
                        instance_name = f"{port_label}.{subkey}{subval}"
                        instances_list.add_instance_unless_exists(instance_name,{})

            else:
                # If the port is just a single value (not a dictionary), we still add it as a sub-instance
                instance_name = f"{port_label}.{value}"
                instances_list.add_instance_unless_exists(instance_name,{})
        
        port_counter += 1

#================ DEFINE CONNECTORS #===============
for instance in instances_list.read_instance_rows():
    instance_name = instance.get("instance_name")
    if instance.get("item_type") == "Connector":
        if instance_name == "X1":
            instances_list.modify(instance_name,{
                "mpn": "D38999_26ZB98PN",
                "supplier": "public"
            })
        else:
            instances_list.modify(instance_name,{
                "mpn": "D38999_26ZA98PN",
                "supplier": "public"
            })

#================ NAME CONNECTORS #===============
for instance in instances_list.read_instance_rows():
    instance_name = instance.get("instance_name")
    if instance_name == "X1":
        instances_list.modify(instance_name,{
            "print_name": "P1"
        })
    elif instance_name == "X2":
        instances_list.modify(instance_name,{
            "print_name": "P2"
        })
    elif instance_name == "X3":
        instances_list.modify(instance_name,{
            "print_name": "P3"
        })
    elif instance_name == "X4":
        instances_list.modify(instance_name,{
            "print_name": "J1"
        })

#================ ASSIGN BACKSHELLS #===============
for instance in instances_list.read_instance_rows():
    instance_name = instance.get("instance_name")
    if instance.get("item_type") == "Connector":
        mpn = instance.get("mpn")
        if re.fullmatch(r"D38999_26ZA.+", mpn):
            if instance.get("print_name") not in ["P3", "J1"]:
                instances_list.add(f"{instance_name}.bs",{
                    "mpn": "M85049-88_9Z03",
                    "supplier": "public",
                    "item_type": "Backshell",
                    "parent_instance": instance.get("instance_name"),
                    "location_is_node_or_segment": "Node"
                })

#=============== ASSIGN PARENTS TO WEIRD PARTS LIKE CONTACTS #===============
for instance in instances_list.read_instance_rows():
    if instance.get("item_type") == "Contact":
        instance_name = instance.get("instance_name")
        prev_port, next_port = instances_list.instance_names_of_adjacent_ports(instance_name)
        prev_port_location_is_node_or_segment = instances_list.attribute_of(prev_port, "location_is_node_or_segment")
        next_port_location_is_node_or_segment = instances_list.attribute_of(next_port, "location_is_node_or_segment")
        if prev_port_location_is_node_or_segment == "Node" and next_port_location_is_node_or_segment == "Segment":
            instances_list.modify(instance_name,{
                "parent_instance": prev_port,
            })
        elif prev_port_location_is_node_or_segment == "Segment" and next_port_location_is_node_or_segment == "Node":
            instances_list.modify(instance_name,{
                "parent_instance": next_port,
            })
        else:
            raise ValueError(f"Because adjacent ports are both port-based or both segment-based, I don't know what parent to assign to {instance_name}")

#================ ASSIGN CABLES #===============
#TODO: UPDATE THIS PER https://github.com/kenyonshutt/harnice/issues/69

#================ GENERATE A WIRELIST BASED ON EXISTING DATA IN INSTANCES_LIST #===============
wirelist.newlist()

#=============== IMPORTING PARTS FROM LIBRARY #===============
print()
print("Importing parts from library")
print(f'{"ITEM NAME":<24}  STATUS')

for instance in instances_list.read_instance_rows():
    instance_name = instance.get("instance_name")
    mpn = instance.get("mpn")

    if instance.get("item_type") in [  # item types to include in import
        "Connector",
        "Backshell"
        ]:

        if instance_name not in [  # instance names to exclude from import
            "X100"
            ]:

            if mpn not in [  # mpns to exclude from import
                "TXPA20"
                ]:

                component_library.pull_part(instance_name)
                # compares existing imported library files against library
                # imports new files if they don't exist
                # if they do exist,
                # checks for updates against the library
                # checks for modifications against the library

#=============== PRODUCING A FORMBOARD BASED ON DEFINED ESCH #===============

print()
print("Validating your formboard graph is structured properly...")
formboard.update_parent_csys()
formboard.update_component_translate()
formboard.validate_nodes()

for instance in instances_list.read_instance_rows():
    if instance.get("item_type") == "Conductor":
        formboard.map_instance_to_segments(instance.get("instance_name"))
exit()

formboard.generate_node_coordinates()
instances_list.add_cable_lengths()
wirelist.add_lengths()
wirelist.tsv_to_xls()
instances_list.add_absolute_angles_to_segments()
instances_list.add_angles_to_nodes()

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
