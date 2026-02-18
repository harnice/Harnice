import csv
import os
import inspect
from threading import Lock
import tempfile
import time
from harnice import fileio, state

COLUMNS = [
    "net", # the physical harness (represented by a net in Kicad) that this instance is part of
    "instance_name", # the unique name of this instance
    "print_name", # the non-unique, human-readable name of this instance, used for printing on output documents
    "bom_line_number", # if this instance represents a physical procurable good, it gets assigned a line number on a bill of materials
    "mfg", # manufacturer of this instance
    "mpn",  # manufacturer part number
    "item_type",  # connector, backshell, whatever
    "parent_instance",  # general purpose reference
    "location_type",  # each instance is either better represented by one or ther other
    "segment_group",  # the group of segments that this instance is part of
    "segment_order",  # the sequential id of this item in its segment group
    "connector_group",  # a group of co-located parts (connectors, backshells, nodes)
    "channel_group", # other instances associated with this one because they are part of the same channel will share this value
    "circuit_id",  # which signal this component is electrically connected to
    "circuit_port_number",  # the sequential id of this item in its signal chain
    "node_at_end_a",  # derived from formboard definition
    "node_at_end_b",  # derived from formboard definition
    "print_name_at_end_a", # human-readable name of this instance if needed, associated with 'node_at_end_a'
    "print_name_at_end_b", # human-readable name of this instance if needed, associated with 'node_at_end_b'
    "parent_csys_instance_name",  # the other instance upon which this instance's location is based
    "parent_csys_outputcsys_name",  # the specific output coordinate system of the parent that this instance's location is based
    "translate_x",  # derived from parent_csys and parent_csys_name
    "translate_y",  # derived from parent_csys and parent_csys_name
    "rotate_csys",  # derived from parent_csys and parent_csys_name
    "absolute_rotation",  # manual add, not nominally used unless it's a flagnote, segment, or node
    "csys_children",  # imported csys children from library attributes file
    "cable_group", # other instances associated with this one because they are part of the same cable will share this value
    "cable_container", # which cable is this instance physically bundled inside of
    "cable_identifier", # cable unique identifier
    "length",  # derived from formboard definition, the length of a segment
    "diameter",  # apparent diameter of a segment <---------- change to print_diameter
    "appearance",  # see harnice.utils.appearance for details
    "note_type",  # build_note, rev_note, etc
    "note_number",  # if there is a counter involved (rev, bom, build_note, etc)
    "note_parent",  # the instance the note applies to. typically don't use this in the instances list, just note_utils
    "note_text",  # the content of the note
    "note_affected_instances",  # list of instances that are affected by the note
    "lib_repo", # publically-traceable URL of the library this instance is from
    "lib_subpath", # path to the instance within the library (directories between the product type and the part number)
    "lib_desc", # description of the instance per the library's revision history
    "lib_latest_rev", # the latest revision of the instance that exists in the remote library
    "lib_rev_used_here", # the revision of the instance that is currently used in this project
    "lib_status", # the status of the instance per the library's revision history
    "lib_releaseticket", #documentation needed
    "lib_datestarted", # the date this instance was first added to the library
    "lib_datemodified", # the date this instance was last modified in the library
    "lib_datereleased", # the date this instance was released in the library, if applicable, per the library's revision history
    "lib_drawnby", # the name of the person who drew the instance, per the library's revision history
    "lib_checkedby", # the name of the person who checked the instance, per the library's revision history
    "project_editable_lib_modified", # a flag to indicate if the imported contents do not match the library's version (it's been locally modified)
    "lib_build_notes", # recommended build notes that come with the instance from the library
    "lib_tools", # recommended tools that come with the instance from the library
    "this_instance_mating_device_refdes",  # if connector, refdes of the device it plugs into
    "this_instance_mating_device_connector",  # if connector, name of the connector it plugs into
    "this_instance_mating_device_connector_mpn",  # if connector, mpn of the connector it plugs into
    "this_net_from_device_refdes", # if this instance is a channel, circuit, conductor, etc, the refdes of the device it interfaces with, just within this net
    "this_net_from_device_channel_id", # if this instance is a channel, circuit, conductor, etc, the channel id in the device it interfaces with, just within this net
    "this_net_from_device_connector_name", # if this instance is a channel, circuit, conductor, etc, the name of the connector it interfaces with, just within this net
    "this_net_to_device_refdes", # if this instance is a channel, circuit, conductor, etc, the refdes of the device it plugs into just within this net
    "this_net_to_device_channel_id", # if this instance is a channel, circuit, conductor, etc, the channel id in the device it plugs into, just within this net
    "this_net_to_device_connector_name", # if this instance is a channel, circuit, conductor, etc, the name of the connector it plugs into, just within this net
    "this_channel_from_device_refdes",  # if this instance is a channel, circuit, conductor, etc, the refdes of the device it interfaces with, at the very end of the channel
    "this_channel_from_device_channel_id", # if this instance is a channel, circuit, conductor, etc, the channel id in the device it interfaces with, at the very end of the channel
    "this_channel_to_device_refdes",  # if this instance is a channel, circuit, conductor, etc, the refdes of the device it plugs into, at the very end of the channel
    "this_channel_to_device_channel_id", # if this instance is a channel, circuit, conductor, etc, the channel id in the device it plugs into, at the very end of the channel
    "this_channel_from_channel_type", # if this instance is a channel, circuit, conductor, etc, the type of the channel it interfaces with, at the very end of the channel
    "this_channel_to_channel_type", # if this instance is a channel, circuit, conductor, etc, the type of the channel it plugs into, at the very end of the channel
    "signal_of_channel_type", # if this instance is a channel, circuit, conductor, etc, the signal of the channel it interfaces with, at the very end of the channel
    "debug", # the call chain of the function that last modified this instance row
    "debug_cutoff", # blank cell to visually cut off the previous column
]


def new_instance(instance_name, instance_data, ignore_duplicates=False):
    """
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
    """
    if instance_name in ["", None]:
        raise ValueError(
            "Argument 'instance_name' is blank and reqired to idenitify a unique instance"
        )

    if (
        "instance_name" in instance_data
        and instance_data["instance_name"] != instance_name
    ):
        raise ValueError(
            f"Inconsistent instance_name: argument='{instance_name}' vs data['instance_name']='{instance_data['instance_name']}'"
        )

    if any(
        row.get("instance_name") == instance_name
        for row in fileio.read_tsv("instances list")
    ):
        if not ignore_duplicates:
            raise ValueError(
                f"An instance with the name '{instance_name}' already exists"
            )
        else:
            return -1

    if instance_data.get("net") is None:
        try:
            instance_data["net"] = state.net
        except AttributeError:  # no net has been set
            pass

    # Add debug call chain
    instance_data["debug"] = _get_call_chain_str()
    instance_data["debug_cutoff"] = " "

    # add argumet to data added
    instance_data["instance_name"] = instance_name

    with open(fileio.path("instances list"), "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS, delimiter="\t")
        writer.writerow({key: instance_data.get(key, "") for key in COLUMNS})


_instances_lock = Lock()


def modify(instance_name, instance_data):
    with _instances_lock:
        path = fileio.path("instances list")

        # --- Read once ---
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter="\t")
            rows = list(reader)
            fieldnames = list(reader.fieldnames or [])

        # --- Add debug info before updating ---
        instance_data["debug"] = _get_call_chain_str()
        instance_data["debug_cutoff"] = " "

        # Ensure any new keys are part of the header
        for key in instance_data:
            if key not in fieldnames:
                fieldnames.append(key)

        # --- Modify in-place ---
        found = False
        for row in rows:
            if row.get("instance_name") == instance_name:
                row.update(instance_data)
                found = True
                break
        if not found:
            raise ValueError(f"Instance '{instance_name}' not found")

        # --- Write atomically ---
        tmp_fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), suffix=".tmp")
        try:
            with os.fdopen(tmp_fd, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")
                writer.writeheader()
                writer.writerows(rows)
                f.flush()
                os.fsync(f.fileno())

            for attempt in range(10):
                try:
                    os.replace(tmp, path)
                    break
                except PermissionError:
                    if attempt == 9:
                        raise
                    time.sleep(0.05 * (attempt + 1))
        except:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise


def remove_instance(instance_to_delete):
    instances_list = fileio.read_tsv("instances list")
    new_list = []
    for instance in instances_list:
        if instance.get("instance_name") == instance_to_delete.get("instance_name"):
            continue
        new_list.append(instance)

    with open(fileio.path("instances list"), "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS, delimiter="\t")
        writer.writeheader()
        writer.writerows(new_list)


def new():
    with open(fileio.path("instances list"), "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS, delimiter="\t")
        writer.writeheader()
        writer.writerows([])


def assign_bom_line_numbers():
    bom = []
    for instance in fileio.read_tsv("instances list"):
        if instance.get("bom_line_number") == "True":
            if instance.get("mpn") == "":
                raise ValueError(
                    f"You've chosen to add {instance.get('instance_name')} to the bom, but haven't specified an MPN"
                )
            if instance.get("mpn") not in bom:
                bom.append(instance.get("mpn"))

    bom_line_number = 1
    for bom_item in bom:
        for instance in fileio.read_tsv("instances list"):
            if instance.get("mpn") == bom_item:
                modify(
                    instance.get("instance_name"), {"bom_line_number": bom_line_number}
                )
        bom_line_number += 1


def attribute_of(target_instance, attribute):
    for instance in fileio.read_tsv("instances list"):
        if instance.get("instance_name") == target_instance:
            return instance.get(attribute)


def instance_in_connector_group_with_item_type(connector_group, item_type):
    if connector_group in ["", None]:
        raise ValueError("Connector group is blank")
    if item_type in ["", None]:
        raise ValueError("Suffix is blank")
    match = 0
    output = None
    for instance in fileio.read_tsv("instances list"):
        if instance.get("connector_group") == connector_group:
            if instance.get("item_type") == item_type:
                match = match + 1
                output = instance
    if match == 0:
        return 0
    if match > 1:
        raise ValueError(
            f"Multiple instances found in connector_group '{connector_group}' with item type '{item_type}'."
        )
    return output


def _get_call_chain_str():
    """
    Returns the call chain as a readable string:
    filename:line in function -> filename:line in function ...
    """
    stack = inspect.stack()
    chain_parts = []
    for frame_info in reversed(stack[1:]):  # skip this function itself
        filename = os.path.basename(frame_info.filename)
        lineno = frame_info.lineno
        function = frame_info.function
        chain_parts.append(f"{filename}:{lineno} in {function}()")
    return " -> ".join(chain_parts)


def list_of_uniques(attribute):
    output = []
    for instance in fileio.read_tsv("instances list"):
        if instance.get(attribute) not in output:
            if instance.get(attribute) not in [None, ""]:
                output.append(instance.get(attribute))
    return output
