import os
import yaml
import re
from harnice import (
    fileio, instances_list, component_library, wirelist,
    svg_outputs, flagnotes, formboard, run_wireviz, rev_history, svg_utils,
    harness_yaml
)

#===========================================================================
#===========================================================================
#             BUILD HARNESS SOURCE OF TRUTH (INSTANCES LIST)
#===========================================================================
#===========================================================================


#=============== CREATE BASE INSTANCES FROM ESCH #===============
# For each electrical circuit (or net) in your system
# Circuit name is a string, ports is a dictionary that contains all the stuff on that circuit
for circuit_name, ports in harness_yaml.load().items():
    instances_list.add(circuit_name,{
        "item_type": "Circuit"
    })
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
                "item_type": "Contact",
                "bom_line_number": True,
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
                    "location_is_node_or_segment": "Node"
                })
            elif re.match(r"C[^.]+", port_label):
                instances_list.add_unless_exists(port_label,{
                    "item_type": "Cable",
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
                            "print_name": subval,
                            "item_type": "Connector cavity",
                            "parent_instance": port_label,
                            "location_is_node_or_segment": "Node",
                            'circuit_id': circuit_name,
                            'circuit_id_port': port_counter
                        })

                    # If the field is "conductor", add a conductor under this wire
                    elif subkey == "conductor":
                        instance_name = f"{port_label}.conductor{subval}"
                        instances_list.add_unless_exists(instance_name,{
                            "print_name": subval,
                            "item_type": "Conductor",
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


#================ ASSIGN MPNS TO CONNECTORS #===============
for instance in instances_list.read_instance_rows():
    instance_name = instance.get("instance_name")
    if instance.get("item_type") == "Connector":
        if instance_name == "X1":
            instances_list.modify(instance_name,{
                "bom_line_number": "True",
                "mpn": "D38999_26ZB98PN",
                "supplier": "public"
            })
        else:
            instances_list.modify(instance_name,{
                "bom_line_number": "True",
                "mpn": "D38999_26ZA98PN",
                "supplier": "public"
            })


#================ ASSIGN PRINT NAMES TO CONNECTORS #===============
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
    elif instance_name == "X500":
        instances_list.modify(instance_name,{
            "print_name": "J2"
        })
    elif instance.get("item_type") == "Connector":
        raise ValueError(f"Connector {instance.get("instance_name")} defined but does not have a print name assigned.")


#================ ASSIGN BACKSHELLS AND ACCESSORIES TO CONNECTORS #===============
for instance in instances_list.read_instance_rows():
    instance_name = instance.get("instance_name")
    if instance.get("item_type") == "Connector":
        mpn = instance.get("mpn")
        if re.fullmatch(r"D38999_26ZA.+", mpn):
            if instance.get("print_name") not in ["P3", "J1"]:
                instances_list.add(f"{instance_name}.bs",{
                    "mpn": "M85049-88_9Z03",
                    "bom_line_number": "True",
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


#================ ASSIGN MPNS TO CABLES #===============
#TODO: UPDATE THIS PER https://github.com/kenyonshutt/harnice/issues/69
for instance in instances_list.read_instance_rows():
    if instance.get("item_type") == "Cable":
        instances_list.modify(instance.get("instance_name"),{
            "mpn": "test",
            "bom_line_number": "True"
        })

#=============== IMPORT PARTS FROM LIBRARY #===============
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


#=============== LOOK INSIDE PART LIBRARIES FOR PREFERRED CSYS PARENTS #===============
#TODO: UPDATE PER https://github.com/kenyonshutt/harnice/issues/181
for instance in instances_list.read_instance_rows():
    if instance.get("item_type") in ["Connector"]:
        formboard.update_parent_csys(instance.get("instance_name"))


#=============== UPDATE FORMBOARD DEFINITION TSV, UPDATE PART PLACEMENT DATA #===============
formboard.update_component_translate()
formboard.validate_nodes()
# map conductors to segments
for instance in instances_list.read_instance_rows():
    if instance.get("item_type") == "Conductor":
        formboard.map_instance_to_segments(instance.get("instance_name"))

# get lengths of conductors
for instance in instances_list.read_instance_rows():
    if instance.get("item_type") == "Conductor":
        conductor_length = 0
        for instance2 in instances_list.read_instance_rows():
            if instance2.get("parent_instance") == instance.get("instance_name"):
                conductor_length += int(instance2.get("length", "").strip()) if instance2.get("length", "").strip() else 0
        instances_list.modify(instance.get("instance_name"), {
            "length": conductor_length
        })

# get lengths of cables (take the length of the longest contained conductor)
for instance in instances_list.read_instance_rows():
    if instance.get("item_type") == "Cable":
        cable_length = 0
        for instance2 in instances_list.read_instance_rows():
            if instance2.get("parent_instance") == instance.get("instance_name"):
                child_length = int(instance2.get("length", "").strip())
                if child_length > cable_length:
                    cable_length = child_length
        instances_list.modify(instance.get("instance_name"), {
            "length": cable_length
        })

formboard.generate_node_coordinates()


#=============== ASSIGN BOM LINE NUMBERS #===============
instances_list.assign_bom_line_numbers()
# bom line numbers will only be assigned to instances that have "bom_line_number" == "True"
# it will replace "True" with a number


#=============== ASSIGN FLAGNOTES #===============
flagnote_counter = 0 # assign a unique ID to each note
buildnote_counter = 1 # buildnotes start at 1

# assign manual flagnotes
flagnotes.ensure_manual_list_exists()
for manual_note in flagnotes.read_manual_list():
    affected_list = manual_note.get("affectedinstances", "").strip().split(",")

    for affected in affected_list:
        instances_list.add_unless_exists(f"flagnote-{flagnote_counter}", {
            "item_type": "Flagnote",
            "note_type": manual_note.get("note_type"),
            "mpn": manual_note.get("shape"),
            "supplier": manual_note.get("shape_supplier"),
            "bubble_text": buildnote_counter, #doesn't matter what you write in bubble_text in the manual file
            "parent_instance": affected,
            "parent_csys": affected,
            "note_text": manual_note.get("note_text")
        })
        flagnote_counter += 1
    
    if manual_note.get("note_type") == "buildnote":
        buildnote_counter += 1

# assign revision history flagnotes
for rev_row in flagnotes.read_revhistory():
    affected_list = rev_row.get("affectedinstances", "").strip().split(",")

    for affected in affected_list:
        instances_list.add_unless_exists(f"flagnote-{flagnote_counter}", {
            "item_type": "Flagnote",
            "note_type": "rev_change_callout",
            "mpn": "rev_change_callout",
            "supplier": "public",
            "bubble_text": rev_row.get("rev"),
            "parent_instance": affected,
            "parent_csys": affected
        })
        flagnote_counter += 1

# assign bom line number flagnotes
for instance in instances_list.read_instance_rows():
    if not instance.get("bom_line_number") == "":
        instances_list.add_unless_exists(f"flagnote-{flagnote_counter}", {
            "item_type": "Flagnote",
            "note_type": "bom_item",
            "mpn": "bom_item",
            "supplier": "public",
            "bubble_text": instance.get("bom_line_number"),
            "parent_instance": instance.get("instance_name"),
            "parent_csys": affected
        })
        flagnote_counter += 1

# assign part name flagnotes
for instance in instances_list.read_instance_rows():
    # most instance types don't need part name flagnotes
    if instance.get("item_type") in ["Connector", "Backshell"]:
        # if there's text in "print_name", prefer that over "instance_name"
        bubble_text = ""
        if instance.get("print_name") == "":
            bubble_text = instance.get("instance_name")
        else:
            bubble_text = instance.get("print_name")

        instances_list.add_unless_exists(f"flagnote-{flagnote_counter}", {
            "item_type": "Flagnote",
            "note_type": "part_name",
            "mpn": "part_name",
            "supplier": "public",
            "bubble_text": bubble_text,
            "parent_instance": instance.get("instance_name"),
            "parent_csys": affected
        })
        flagnote_counter += 1

#======== add funky flagnote rules
# do not add bom bubbles for contacts, but instead a buildnote
contact_flagnote_conversion_happened = False
for instance in instances_list.read_instance_rows():
    if instance.get("item_type") == "Flagnote":
        if instances_list.attribute_of(instance.get("parent_instance"), "item_type") == "Contact":
            #TODO: DELETE AN INSTANCE FROM INSTANCES LIST
            #https://github.com/kenyonshutt/harnice/issues/224
            #instances_list.delete_instance(instance.get("instance_name"))
            instances_list.modify(instance.get("instance_name"), {
                "item_type": "DELETEME"
            })

            instances_list.add_unless_exists(f"flagnote-{flagnote_counter}", {
                "item_type": "Flagnote",
                "note_type": "buildnote",
                "mpn": "buildnote",
                "supplier": "public",
                "bubble_text": buildnote_counter,
                "parent_instance": instance.get("parent_instance"),
                "parent_csys": instance.get("parent_instance"),
                "note_text": "Special contacts used in this connector. Refer to wirelist for details"
            })
            flagnote_counter += 1
            contact_flagnote_conversion_happened = True
if contact_flagnote_conversion_happened == True:
    buildnote_counter += 1

flagnotes.compile_buildnotes():
    # add buildnote itemtypes to list, intended to make buildnote list unique

#TODO: add buildnote locations per https://github.com/kenyonshutt/harnice/issues/181

#===========================================================================
#===========================================================================
#                      CONSTRUCT HARNESS ARTIFACTS
#===========================================================================
#===========================================================================


#=============== MAKE A WIRELIST #===============
wirelist.newlist(
    [
        {"name": "Circuit_name", "fill": "black", "font": "white"},
        {"name": "Length", "fill": "black", "font": "white"},
        {"name": "Cable", "fill": "black", "font": "white"},
        {"name": "Conductor_identifier", "fill": "black", "font": "white"},

        {"name": "From_connector", "fill": "green", "font": "white"},
        {"name": "From_connector_cavity", "fill": "green", "font": "white"},
        {"name": "From_special_contact", "fill": "green", "font": "white"},

        {"name": "To_special_contact", "fill": "red", "font": "white"},
        {"name": "To_connector", "fill": "red", "font": "white"},
        {"name": "To_connector_cavity", "fill": "red", "font": "white"}
    ]
)

# search through all the circuits in the instances list
for instance in instances_list.read_instance_rows():
    length = ""
    cable = ""
    conductor_identifier = ""
    from_connector = ""
    from_connector_cavity = ""
    from_special_contact = ""
    to_special_contact = ""
    to_connector = ""
    to_connector_cavity = ""

    if instance.get("item_type") == "Circuit":
        circuit_name = instance.get("instance_name")

        # look for "From" and "To" connectors and cavities by cavity
        connector_cavity_counter = 0
        for instance3 in instances_list.read_instance_rows():
            if instance3.get("circuit_id") == circuit_name:
                if instance3.get("item_type") == "Connector cavity":
                    if connector_cavity_counter == 0:
                        from_connector_cavity = instance3.get("instance_name")
                        from_connector = instances_list.attribute_of(from_connector_cavity, "parent_instance")
                    elif connector_cavity_counter == 1:
                        to_connector_cavity = instance3.get("instance_name")
                        to_connector = instances_list.attribute_of(to_connector_cavity, "parent_instance")
                    else:
                        raise ValueError(f"There are 3 or more cavities specified in circuit {circuit_name} but expected two (to, from) when building wirelist.")
                    connector_cavity_counter += 1

        # look for cavities that have parents that match a to or from connector
        for instance4 in instances_list.read_instance_rows():
            if instance4.get("circuit_id") == circuit_name:
                if instance4.get("item_type") == "Contact":
                    if instance4.get("parent_instance") == from_connector:
                        from_special_contact = instance4.get("instance_name")
                    elif instance4.get("parent_instance") == to_connector:
                        to_special_contact = instance4.get("instance_name")

        # find conductor and cable
        for instance5 in instances_list.read_instance_rows():
            if instance5.get("circuit_id") == circuit_name:
                if instance5.get("item_type") == "Conductor":
                    conductor_identifier = instance5.get("print_name")
                    cable = instance5.get("parent_instance")
                    length = instance5.get("length")
                    
        wirelist.add({
            "Circuit_name": circuit_name,
            "Length": length,
            "Cable": cable,
            "Conductor_identifier": conductor_identifier,
            "From_connector": instances_list.attribute_of(from_connector, "print_name"),
            "From_connector_cavity": instances_list.attribute_of(from_connector_cavity, "print_name"),
            "From_special_contact": from_special_contact,
            "To_special_contact": to_special_contact,
            "To_connector": instances_list.attribute_of(to_connector, "print_name"),
            "To_connector_cavity": instances_list.attribute_of(to_connector_cavity, "print_name"),
        })

#=============== MAKE A PRETTY WIRELIST #===============
wirelist.tsv_to_xls()

#=============== MAKE A BOM #===============
instances_list.export_bom(12) # arg: cable margin per cut

exit()

#=============== RUN WIREVIZ #===============
run_wireviz.generate_esch()

#=============== REBUILDING OUTPUT SVG #===============
# ensure page setup is defined, if not, make a basic one
page_setup_contents = svg_outputs.update_page_setup_json()

revinfo = rev_history.revision_info()
rev_history.update_datemodified()

# add parent types to make filtering easier
instances_list.add_parent_instance_type()

# prepare the building blocks as svgsflagnotes.make_note_drawings()
flagnotes.make_leader_drawings()
svg_outputs.prep_formboard_drawings(page_setup_contents)
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
