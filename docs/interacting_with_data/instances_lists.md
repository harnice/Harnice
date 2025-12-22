## What it is
`*-instances_list.tsv` is a tab-separated value list of every physical or notional thing, drawing element, or concept that is the single source of truth for the product you are working on.

## How to Import
Including the instances list module into your py file will allow you to access the functions of this module. Copy and paste it into the top of your py file.
`from harnice.lists import instances_list`

## Columns
``` py
    "net",
    "instance_name",
    "print_name",
    "bom_line_number",
    "mfg",
    "mpn",  # unique part identifier (manufacturer + part number concatenated)
    "item_type",  # connector, backshell, whatever
    "parent_instance",  # general purpose reference
    "location_type",  # each instance is either better represented by one or ther other
    "segment_group",  # the group of segments that this instance is part of
    "segment_order",  # the sequential id of this item in its segment group
    "connector_group",  # a group of co-located parts (connectors, backshells, nodes)
    "channel_group",
    "circuit_id",  # which signal this component is electrically connected to
    "circuit_port_number",  # the sequential id of this item in its signal chain
    "node_at_end_a",  # derived from formboard definition
    "node_at_end_b",  # derived from formboard definition
    "parent_csys_instance_name",  # the other instance upon which this instance's location is based
    "parent_csys_outputcsys_name",  # the specific output coordinate system of the parent that this instance's location is based
    "translate_x",  # derived from parent_csys and parent_csys_name
    "translate_y",  # derived from parent_csys and parent_csys_name
    "rotate_csys",  # derived from parent_csys and parent_csys_name
    "absolute_rotation",  # manual add, not nominally used unless it's a flagnote, segment, or node
    "csys_children",  # imported csys children from library attributes file
    "cable_group",
    "cable_container",
    "cable_identifier",
    "length",  # derived from formboard definition, the length of a segment
    "diameter",  # apparent diameter of a segment <---------- change to print_diameter
    "appearance",  # see harnice.utils.appearance for details
    "note_type",  # build_note, rev_note, etc
    "note_number",  # if there is a counter involved (rev, bom, build_note, etc)
    "note_parent",  # the instance the note applies to. typically don't use this in the instances list, just note_utils
    "note_text",  # the content of the note
    "note_affected_instances",  # list of instances that are affected by the note
    "lib_repo",
    "lib_subpath",
    "lib_desc",
    "lib_latest_rev",
    "lib_rev_used_here",
    "lib_status",
    "lib_releaseticket",
    "lib_datestarted",
    "lib_datemodified",
    "lib_datereleased",
    "lib_drawnby",
    "lib_checkedby",
    "project_editable_lib_modified",
    "lib_build_notes",
    "lib_tools",
    "this_instance_mating_device_refdes",  # if connector, refdes of the device it plugs into
    "this_instance_mating_device_connector",  # if connector, name of the connector it plugs into
    "this_instance_mating_device_connector_mpn",  # if connector, mpn of the connector it plugs into
    "this_net_from_device_refdes",
    "this_net_from_device_channel_id",
    "this_net_from_device_connector_name",
    "this_net_to_device_refdes",
    "this_net_to_device_channel_id",
    "this_net_to_device_connector_name",
    "this_channel_from_device_refdes",  # if channel, refdes of the device on one side of the channel
    "this_channel_from_device_channel_id",
    "this_channel_to_device_refdes",  # if channel, refdes of the device on the other side of the channel
    "this_channel_to_device_channel_id",
    "this_channel_from_channel_type",
    "this_channel_to_channel_type",
    "signal_of_channel_type",
    "debug",
    "debug_cutoff",
```
## Commands

??? info "New Instance"

    ```py
    instances_list.new_instance(
        instance_name,
        instance_data,
        ignore_duplicates=False
    )
    ```

    Add a new instance to your instances list.

    - `instance_name` is a string and must be unique within the list.
    - `instance_data` is a dictionary of columns (above). You may or may not include `instance_name` in this dict, though if you do and it doesn't match the argument, the code will fail.
    - Setting `ignore_duplicates` to `True` will cause the line to pass silently if you try to add an instance with an instance_name that already exists. By default, `False`, if you do this, the code will raise an error if you try to add a duplicate instance_name.

??? info "Modify"

    ```py
    instances_list.modify(
        instance_name,
        instance_data
    )
    ```
    TODO:DESCRIPTION NEEDED

??? info "Remove Instance"

    ```py
    instances_list.remove_instance(
        instance_to_delete
    )
    ```
    TODO:DESCRIPTION NEEDED

??? info "New"

    ```py
    instances_list.new()
    ```
    TODO:DESCRIPTION NEEDED

??? info "Assign Bom Line Numbers"

    ```py
    instances_list.assign_bom_line_numbers():
    ```
    TODO:DESCRIPTION NEEDED

??? info "Attribute Of"

    ```py
    instances_list.attribute_of():
    ```
    TODO:DESCRIPTION NEEDED

??? info "Instance In Connector Group With Item"

    ```py
    instances_list.instance_in_connector_group_with_item_type():
    ```
    TODO:DESCRIPTION NEEDED

??? info "List of Uniques"

    ```py
    instances_list.list_of_uniques(
        attribute
    ):
    ```
    TODO:DESCRIPTION NEEDED