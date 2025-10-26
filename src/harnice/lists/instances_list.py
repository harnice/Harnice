import csv
import os
import inspect
from threading import Lock
from harnice import fileio

COLUMNS = [
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
    "absolute_rotation",  # manual add, not nominally used unless it's a flagnote
    "cable_group",
    "cable_container",
    "cable_identifier",
    "length",  # derived from formboard definition, the length of a segment
    "diameter",  # apparent diameter of a segment <---------- change to print_diameter
    "note_type",
    "note_number",  # <--------- merge with parent_csys and import instances of child csys?
    "bubble_text",
    "note_text",
    "lib_repo",
    "lib_subpath" "lib_desc",
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
]


def new_instance(instance_name, instance_data, ignore_duplicates=False):
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

    # TODO #467: re-add this when we have a way to set the net
    # if fileio.get_net() and fileio.product_type == "harness":
    # instance_data["net"] = fileio.get_net()

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
            fieldnames = reader.fieldnames or []

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
        tmp = path + ".tmp"
        with open(tmp, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")
            writer.writeheader()
            writer.writerows(rows)
            f.flush()
            os.fsync(f.fileno())

        os.replace(tmp, path)


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


def add_revhistory_of_imported_part(instance_name, rev_data):
    # Expected rev_data is a dict with keys from rev_history.COLUMNS
    with open(fileio.path("instances list"), newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        rows = list(reader)
        fieldnames = reader.fieldnames

    for row in rows:
        if row.get("instance_name") == instance_name:
            row["lib_latest_rev"] = str(rev_data.get("rev", ""))
            row["lib_rev_used_here"] = str(rev_data.get("rev", ""))
            row["lib_status"] = rev_data.get("status", "")
            row["lib_datemodified"] = rev_data.get("datemodified", "")
            row["lib_datereleased"] = rev_data.get("datereleased", "")
            row["lib_drawnby"] = rev_data.get("drawnby", "")
            break  # instance_name is unique

    with open(fileio.path("instances list"), "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


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
