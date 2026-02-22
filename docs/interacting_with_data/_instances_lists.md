## Interacting with Instances Lists
An instances list is a list of every physical or notional item, idea, note, part, instruction, circuit, drawing element, thing, concept literally anything that describes how to build that harness or system.

Instances lists are the single comprehensive source of truth for the product you are working on. Other documents like the Feature Tree, etc, build this list, and all output documentation are derived from it.

---
##Columns 
*Columns are automatically generated when `instances_list.new()` is called. Additional columns are not supported and may result in an error when parsing.*
=== "`net`"

    the physical harness (represented by a net in Kicad) that this instance is part of

=== "`instance_name`"

    the unique name of this instance

=== "`print_name`"

    the non-unique, human-readable name of this instance, used for printing on output documents

=== "`bom_line_number`"

    if this instance represents a physical procurable good, it gets assigned a line number on a bill of materials

=== "`mfg`"

    manufacturer of this instance

=== "`mpn`"

    manufacturer part number

=== "`item_type`"

    connector, backshell, whatever

=== "`parent_instance`"

    general purpose reference

=== "`location_type`"

    each instance is either better represented by one or ther other

=== "`segment_group`"

    the group of segments that this instance is part of

=== "`segment_order`"

    the sequential id of this item in its segment group

=== "`connector_group`"

    a group of co-located parts (connectors, backshells, nodes)

=== "`channel_group`"

    other instances associated with this one because they are part of the same channel will share this value

=== "`circuit_id`"

    which signal this component is electrically connected to

=== "`circuit_port_number`"

    the sequential id of this item in its signal chain

=== "`node_at_end_a`"

    derived from formboard definition

=== "`node_at_end_b`"

    derived from formboard definition

=== "`print_name_at_end_a`"

    human-readable name of this instance if needed, associated with 'node_at_end_a'

=== "`print_name_at_end_b`"

    human-readable name of this instance if needed, associated with 'node_at_end_b'

=== "`parent_csys_instance_name`"

    the other instance upon which this instance's location is based

=== "`parent_csys_outputcsys_name`"

    the specific output coordinate system of the parent that this instance's location is based

=== "`translate_x`"

    derived from parent_csys and parent_csys_name

=== "`translate_y`"

    derived from parent_csys and parent_csys_name

=== "`rotate_csys`"

    derived from parent_csys and parent_csys_name

=== "`absolute_rotation`"

    manual add, not nominally used unless it's a flagnote, segment, or node

=== "`csys_children`"

    imported csys children from library attributes file

=== "`cable_group`"

    other instances associated with this one because they are part of the same cable will share this value

=== "`cable_container`"

    which cable is this instance physically bundled inside of

=== "`cable_identifier`"

    cable unique identifier

=== "`length`"

    derived from formboard definition, the length of a segment

=== "`length_tolerance`"

    derived from formboard definition, the tolerance on the length of a segment

=== "`diameter`"

    apparent diameter of a segment <---------- change to print_diameter

=== "`appearance`"

    see harnice.utils.appearance for details

=== "`note_type`"

    build_note, rev_note, etc

=== "`note_number`"

    if there is a counter involved (rev, bom, build_note, etc)

=== "`note_parent`"

    the instance the note applies to. typically don't use this in the instances list, just note_utils

=== "`note_text`"

    the content of the note

=== "`note_affected_instances`"

    list of instances that are affected by the note

=== "`lib_repo`"

    publically-traceable URL of the library this instance is from

=== "`lib_subpath`"

    path to the instance within the library (directories between the product type and the part number)

=== "`lib_desc`"

    description of the instance per the library's revision history

=== "`lib_latest_rev`"

    the latest revision of the instance that exists in the remote library

=== "`lib_rev_used_here`"

    the revision of the instance that is currently used in this project

=== "`lib_status`"

    the status of the instance per the library's revision history

=== "`lib_releaseticket`"

    documentation needed

=== "`lib_datestarted`"

    the date this instance was first added to the library

=== "`lib_datemodified`"

    the date this instance was last modified in the library

=== "`lib_datereleased`"

    the date this instance was released in the library, if applicable, per the library's revision history

=== "`lib_drawnby`"

    the name of the person who drew the instance, per the library's revision history

=== "`lib_checkedby`"

    the name of the person who checked the instance, per the library's revision history

=== "`project_editable_lib_modified`"

    a flag to indicate if the imported contents do not match the library's version (it's been locally modified)

=== "`lib_build_notes`"

    recommended build notes that come with the instance from the library

=== "`lib_tools`"

    recommended tools that come with the instance from the library

=== "`this_instance_mating_device_refdes`"

    if connector, refdes of the device it plugs into

=== "`this_instance_mating_device_connector`"

    if connector, name of the connector it plugs into

=== "`this_instance_mating_device_connector_mpn`"

    if connector, mpn of the connector it plugs into

=== "`this_net_from_device_refdes`"

    if this instance is a channel, circuit, conductor, etc, the refdes of the device it interfaces with, just within this net

=== "`this_net_from_device_channel_id`"

    if this instance is a channel, circuit, conductor, etc, the channel id in the device it interfaces with, just within this net

=== "`this_net_from_device_connector_name`"

    if this instance is a channel, circuit, conductor, etc, the name of the connector it interfaces with, just within this net

=== "`this_net_to_device_refdes`"

    if this instance is a channel, circuit, conductor, etc, the refdes of the device it plugs into just within this net

=== "`this_net_to_device_channel_id`"

    if this instance is a channel, circuit, conductor, etc, the channel id in the device it plugs into, just within this net

=== "`this_net_to_device_connector_name`"

    if this instance is a channel, circuit, conductor, etc, the name of the connector it plugs into, just within this net

=== "`this_channel_from_device_refdes`"

    if this instance is a channel, circuit, conductor, etc, the refdes of the device it interfaces with, at the very end of the channel

=== "`this_channel_from_device_channel_id`"

    if this instance is a channel, circuit, conductor, etc, the channel id in the device it interfaces with, at the very end of the channel

=== "`this_channel_to_device_refdes`"

    if this instance is a channel, circuit, conductor, etc, the refdes of the device it plugs into, at the very end of the channel

=== "`this_channel_to_device_channel_id`"

    if this instance is a channel, circuit, conductor, etc, the channel id in the device it plugs into, at the very end of the channel

=== "`this_channel_from_channel_type`"

    if this instance is a channel, circuit, conductor, etc, the type of the channel it interfaces with, at the very end of the channel

=== "`this_channel_to_channel_type`"

    if this instance is a channel, circuit, conductor, etc, the type of the channel it plugs into, at the very end of the channel

=== "`signal_of_channel_type`"

    if this instance is a channel, circuit, conductor, etc, the signal of the channel it interfaces with, at the very end of the channel

=== "`debug`"

    the call chain of the function that last modified this instance row

=== "`debug_cutoff`"

    blank cell to visually cut off the previous column


---
##Commands:
*Use the following functions by first importing the module in your script like this: 
```python
from harnice.lists import instances_list
```
 then use as written.*
??? info "`instances_list.new_instance(instance_name, instance_data, ignore_duplicates=False)`"

    New Instance
    
    instances_list.new_instance(
        instance_name,
        instance_data,
        ignore_duplicates=False
    )
    
    Add a new instance to your instances list.
    
        instance_name is a string and must be unique within the list.
        instance_data is a dictionary of columns (above). You may or may not include instance_name in this dict, though if you do and it doesn't match the argument, the code will fail.
        Setting ignore_duplicates to True will cause the line to pass silently if you try to add an instance with an instance_name that already exists. By default, False, if you do this, the code will raise an error if you try to add a duplicate instance_name.
    
        Args:
            instance_name: string, must be unique within the list
            instance_data: dictionary of columns (above)
            ignore_duplicates: boolean, default False
    
        Returns:
            -1 if the instance was added successfully, otherwise raises an error

??? info "`instances_list.modify(instance_name, instance_data)`"

    Documentation needed.

??? info "`instances_list.remove_instance(instance_to_delete)`"

    Documentation needed.

??? info "`instances_list.new()`"

    Documentation needed.

??? info "`instances_list.assign_bom_line_numbers()`"

    Documentation needed.

??? info "`instances_list.attribute_of(target_instance, attribute)`"

    Documentation needed.

??? info "`instances_list.instance_in_connector_group_with_item_type(connector_group, item_type)`"

    Documentation needed.

??? info "`instances_list.list_of_uniques(attribute)`"

    Documentation needed.

