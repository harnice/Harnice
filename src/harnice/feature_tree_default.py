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