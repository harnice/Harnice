from pathlib import Path
from docs_compiler import print_function_docs
from harnice.lists import channel_map, circuits_list, disconnect_map, formboard_graph, instances_list, library_history, post_harness_instances_list, rev_history, signals_list

#========================================================
# CHANNEL MAPS
#========================================================
module_prefix = "channel_map"
md = ["""# Interacting with Channel Maps

A list of channels on devices within merged_nets that are either mapped to other channels or are unmapped.
"""]

md.append("\n##Commands:\n")
md.append(print_function_docs(channel_map.new, module_prefix))
md.append(print_function_docs(channel_map.map, module_prefix))
md.append(print_function_docs(channel_map.already_mapped_set_append, module_prefix))
md.append(print_function_docs(channel_map.already_mapped_set, module_prefix))
md.append(print_function_docs(channel_map.already_mapped, module_prefix))

harnice_dir = Path(__file__).resolve().parents[1]
path = harnice_dir / "docs" / "interacting_with_data" / "channel_maps.md"
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text("".join(md), encoding="utf-8")

#========================================================
# CIRCUITS LISTS
#========================================================
module_prefix = "circuits_list"

md = [r"""# Interacting with Circuits Lists

A list of every individual electrical connection that must be present in your system or harness to satisfy your channel and disconnect maps.
"""]

md.append("\n##Commands: test\n")
md.append(print_function_docs(circuits_list.new, module_prefix))

harnice_dir = Path(__file__).resolve().parents[1]
path = harnice_dir / "docs" / "interacting_with_data" / "circuits_lists.md"
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text("".join(md), encoding="utf-8")

#========================================================
# DISCONNECT MAPS
#========================================================
module_prefix = "disconnect_map"

md = ["""# Interacting with Disconnect Maps

A list of every available channel on a every disconnect, and every channel that may or may not pass through it
"""]

harnice_dir = Path(__file__).resolve().parents[1]
path = harnice_dir / "docs" / "interacting_with_data" / "disconnect_maps.md"

#========================================================
# FORMBOARD GRAPHS
#========================================================
module_prefix = "formboard_graph"

md = ["""# Interacting with Formboard Graphs"""]

harnice_dir = Path(__file__).resolve().parents[1]
path = harnice_dir / "docs" / "interacting_with_data" / "formboard_graphs.md"

#========================================================
# INSTANCES LISTS
#========================================================
module_prefix = "instances_list"

md = ["""## What it is
`*-instances_list.tsv` is a tab-separated value list of every physical or notional thing, drawing element, or concept that is the single source of truth for the product you are working on.

A list of every single item, idea, note, part, instruction, circuit, literally anything that comprehensively describes how to build that harness or system
TSV (tab-separated-values, big spreadsheet)
Declined alternatives: STEP files, schematics, dictionaries not general, descriptive, or human readable enough


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
    TODO:DESCRIPTION NEEDED"""]

harnice_dir = Path(__file__).resolve().parents[1]
path = harnice_dir / "docs" / "interacting_with_data" / "instances_lists.md"
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text("".join(md), encoding="utf-8")

#========================================================
# LIBRARY HISTORY
#========================================================
module_prefix = "library_history"

md = ["""# Interacting with Library History

A report of what was imported during the most recent render of the current product
"""]

harnice_dir = Path(__file__).resolve().parents[1]
path = harnice_dir / "docs" / "interacting_with_data" / "library_history.md"
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text("".join(md), encoding="utf-8")

#========================================================
# NETLISTS
#========================================================

md = ["""# Interacting with Netlists"""]

harnice_dir = Path(__file__).resolve().parents[1]
path = harnice_dir / "docs" / "interacting_with_data" / "netlists.md"
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text("".join(md), encoding="utf-8")

#========================================================
# POST-HARNESS INSTANCES LISTS
#========================================================

md = ["""# Interacting with Post Harness Instances Lists

A list of every physical or notional thing, drawing element, or concept that includes instances added at the harness level, that represents a system
"""]

harnice_dir = Path(__file__).resolve().parents[1]
path = harnice_dir / "docs" / "interacting_with_data" / "post_harness_instances_lists.md"
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text("".join(md), encoding="utf-8")

#========================================================
# REVISION HISTORY LISTS
#========================================================
module_prefix = "revision_history_list"

md = ["""# Interacting with Revision History Lists

A record of every revision of a part, and its release status
"""]

harnice_dir = Path(__file__).resolve().parents[1]
path = harnice_dir / "docs" / "interacting_with_data" / "revision_history_lists.md"
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text("".join(md), encoding="utf-8")

#========================================================
# SIGNALS LISTS
#========================================================
module_prefix = "signals_list"

md = ["""A **Signals List** is an exhaustive list of every signal is going into or out of a thing. Signals Lists are the primary way Harnice stores information about devices, and act as the source of truth for devices and disconnects.

 - Each signal is contained by one or more cavities of connectors
 - Each signal may be assigned to a functional signal of a channel, or left unused.


---

## Columns

### Signals Lists for Devices

=== "`channel_id`"

    Unique identifier for the channel. 

=== "`signal`"

    Name of the electrical function of that signal, as it pertains to its channel type defition. i.e. "positive"

=== "`connector_name`"

    Unique identifier for the connector that this signal and channel is a part of.

=== "`cavity`"

    Identifier of the pin, socket, stud, etc, that this signal is internally electrically routed to within its connector.

=== "`connector_mpn`"

    MPN of the connector in this device (NOT the mating connector).

=== "`channel_type`"

    {% include-markdown "fragments/channel_type_reference.md" %}


### Signals Lists for Disconnects

=== "`channel_id`"

    Unique identifier for the channel. 

=== "`signal`"

    Name of the electrical function of that signal, as it pertains to its channel type defition. i.e. "positive"

=== "`A, B_cavity`"

    Identifier of the pin, socket, stud, etc, that this signal is internally electrically routed to within that side of the connector.

    ??? question "Why are A and B different here?"

        Sometimes it's possible to have connectors that have cavities that may mate electrically, but have different names. For example, suppose two connectors physically mate, but are made by different manufacturers. One manufacturer used lowercase (a, b, c) to reference the cavities but the other used uppercase (A, B, C), or numbers (1, 2, 3), or colors (red, green, blue), etc.

=== "`A, B_connector_mpn`"

    MPN of the connector of the harness on this side of the disconnect

=== "`A, B_channel_type`"

    The channel type of this side of the discconect.

    ??? question "Why are A and B different here?"

        It's important to keep track of which side has which channel type so that you cannot accidentally flip pins and sockets, for example, by mapping the wrong channel type to the wrong pin gender. Careful validation should be done when mapping channels through disconnects to ensure the disconnects have channels that pass through them in the correct direction.

---

## Signals Lists have rules...

 - Every combination of (channel_id, signal) must be unique within the signals list
    - i.e. you can’t have two “ch1, pos” signals on the same device

 - Signals of channels in a signals list must agree with their channel type definitions
    - If a signal is on the list that has a channel name and a channel type, all of the required signals of that channel type must also be present in the list with the same channel name (you can't just define 'positive' if the channel type requires 'positive' and 'negative')

 - Every signal in the Signals List must have a pre-defined channel type

    ??? info "Channel Types"
        {% include-markdown "products/channel_type.md" %}

 - You can’t put signals of the same channel on different connectors
    - While this may sound inconvenient, it breaks a lot of internal assumptions Harnice is making on the back end about how to map channels. 

    - If you need to do this, I recommend the following two options:
    
        - **Most correct but confusing:** Define one channel type per signal, then manually chmap your channels or write a macro for mapping the channels to their respective destinations.

        - **Janky but easiest to understand:** Define a connector part number that actually represents multiple connectors, while using cavities to reference each connector.

 - “A” and “B” channels of the same disconnect must be compatible with each other"""]

harnice_dir = Path(__file__).resolve().parents[1]
path = harnice_dir / "docs" / "interacting_with_data" / "signals_lists.md"
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text("".join(md), encoding="utf-8")

#========================================================
# SYSTEM MANIFESTS
#========================================================
module_prefix = "system_manifest"

md = ["""# Interacting with System Manifests

A table that relates reference designator to part number(s), and may contain other information indexed to the reference designator
"""]

harnice_dir = Path(__file__).resolve().parents[1]
path = harnice_dir / "docs" / "interacting_with_data" / "system_manifests.md"