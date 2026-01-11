## Interacting with Instances Lists
An instances list is a list of every physical or notional item, idea, note, part, instruction, circuit, drawing element, thing, concept literally anything that describes how to build that harness or system.

Instances lists are the single comprehensive source of truth for the product you are working on. Other documents like the Feature Tree, etc, build this list, and all output documentation are derived from it.

---
## Columns 
=== "`net`"

    documentation needed

=== "`instance_name`"

    documentation needed

=== "`print_name`"

    documentation needed

=== "`bom_line_number`"

    documentation needed

=== "`mfg`"

    documentation needed

=== "`mpn`"

    unique part identifier (manufacturer + part number concatenated)

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

    documentation needed

=== "`circuit_id`"

    which signal this component is electrically connected to

=== "`circuit_port_number`"

    the sequential id of this item in its signal chain

=== "`node_at_end_a`"

    derived from formboard definition

=== "`node_at_end_b`"

    derived from formboard definition

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

    documentation needed

=== "`cable_container`"

    documentation needed

=== "`cable_identifier`"

    documentation needed

=== "`length`"

    derived from formboard definition, the length of a segment

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

    documentation needed

=== "`lib_subpath`"

    documentation needed

=== "`lib_desc`"

    documentation needed

=== "`lib_latest_rev`"

    documentation needed

=== "`lib_rev_used_here`"

    documentation needed

=== "`lib_status`"

    documentation needed

=== "`lib_releaseticket`"

    documentation needed

=== "`lib_datestarted`"

    documentation needed

=== "`lib_datemodified`"

    documentation needed

=== "`lib_datereleased`"

    documentation needed

=== "`lib_drawnby`"

    documentation needed

=== "`lib_checkedby`"

    documentation needed

=== "`project_editable_lib_modified`"

    documentation needed

=== "`lib_build_notes`"

    documentation needed

=== "`lib_tools`"

    documentation needed

=== "`this_instance_mating_device_refdes`"

    if connector, refdes of the device it plugs into

=== "`this_instance_mating_device_connector`"

    if connector, name of the connector it plugs into

=== "`this_instance_mating_device_connector_mpn`"

    if connector, mpn of the connector it plugs into

=== "`this_net_from_device_refdes`"

    documentation needed

=== "`this_net_from_device_channel_id`"

    documentation needed

=== "`this_net_from_device_connector_name`"

    documentation needed

=== "`this_net_to_device_refdes`"

    documentation needed

=== "`this_net_to_device_channel_id`"

    documentation needed

=== "`this_net_to_device_connector_name`"

    documentation needed

=== "`this_channel_from_device_refdes`"

    if channel, refdes of the device on one side of the channel

=== "`this_channel_from_device_channel_id`"

    documentation needed

=== "`this_channel_to_device_refdes`"

    if channel, refdes of the device on the other side of the channel

=== "`this_channel_to_device_channel_id`"

    documentation needed

=== "`this_channel_from_channel_type`"

    documentation needed

=== "`this_channel_to_channel_type`"

    documentation needed

=== "`signal_of_channel_type`"

    documentation needed

=== "`debug`"

    documentation needed

=== "`debug_cutoff`"

    documentation needed


##Commands:
??? info "`instances_list.new_instance()`"

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

??? info "`instances_list.modify()`"

    Documentation needed.

??? info "`instances_list.remove_instance()`"

    Documentation needed.

??? info "`instances_list.new()`"

    Documentation needed.

??? info "`instances_list.assign_bom_line_numbers()`"

    Documentation needed.

??? info "`instances_list.attribute_of()`"

    Documentation needed.

??? info "`instances_list.instance_in_connector_group_with_item_type()`"

    Documentation needed.

??? info "`instances_list.list_of_uniques()`"

    Documentation needed.

