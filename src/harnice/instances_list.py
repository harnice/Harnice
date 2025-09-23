import csv
import os
import inspect
from harnice import fileio, system_utils, icd

RECOGNIZED_ITEM_TYPES = {"Segment", "Node", "Flagnote", "Flagnote leader", "Location"}

INSTANCES_LIST_COLUMNS = [
    "net",
    "instance_name",
    "print_name",
    "bom_line_number",
    "mpn",  # unique part identifier (manufacturer + part number concatenated)
    "item_type",  # connector, backshell, whatever
    "parent_instance",  # general purpose reference
    "location_is_node_or_segment",  # each instance is either better represented by one or ther other
    "cluster",  # a group of co-located parts (connectors, backshells, nodes)
    "circuit_id",  # which signal this component is electrically connected to
    "circuit_id_port",  # the sequential id of this item in its signal chain
    "length",  # derived from formboard definition, the length of a segment
    "diameter",  # apparent diameter of a segment <---------- change to print_diameter
    "node_at_end_a",  # derived from formboard definition
    "node_at_end_b",  # derived from formboard definition
    "parent_csys_instance_name",  # the other instance upon which this instance's location is based
    "parent_csys_outputcsys_name",  # the specific output coordinate system of the parent that this instance's location is based
    "translate_x",  # derived from parent_csys and parent_csys_name
    "translate_y",  # derived from parent_csys and parent_csys_name
    "rotate_csys",  # derived from parent_csys and parent_csys_name
    "absolute_rotation",  # manual add, not nominally used unless it's a flagnote
    "note_type",
    "note_number",  # <--------- merge with parent_csys and import instances of child csys?
    "bubble_text",
    "note_text",
    "lib_repo",
    "lib_latest_rev",
    "lib_rev_used_here",
    "lib_status",
    "lib_datemodified",
    "lib_datereleased",
    "lib_drawnby",
    "debug",
    "debug_cutoff",
]


def read_instance_rows():
    with open(fileio.path("instances list"), newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def add_unless_exists(instance_name, instance_data):
    """
    Adds a new instance to the instances list TSV, unless one with the same
    name already exists.

    Args:
        instance_name (str): The name of the instance to add.
        instance_data (dict): Dictionary of instance attributes. May include "instance_name".

    Returns:
        bool: True if the instance already existed (no write performed),
              False if a new row was written.

    Raises:
        ValueError: If instance_name is missing, or if instance_name and
                    instance_data["instance_name"] disagree.
    """
    if not instance_name:
        raise ValueError("Missing required argument: 'instance_name'")

    if (
        "instance_name" in instance_data
        and instance_data["instance_name"] != instance_name
    ):
        raise ValueError(
            f"Inconsistent instance_name: argument='{instance_name}' vs data['instance_name']='{instance_data['instance_name']}'"
        )

    instance_data["instance_name"] = instance_name  # Ensure consistency

    # Add debug call chain
    instance_data["debug"] = get_call_chain_str()
    instance_data["debug_cutoff"] = " "

    instances = read_instance_rows()
    if any(row.get("instance_name") == instance_name for row in instances):
        return True  # Already exists

    with open(fileio.path("instances list"), "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=INSTANCES_LIST_COLUMNS, delimiter="\t")
        writer.writerow(
            {key: instance_data.get(key, "") for key in INSTANCES_LIST_COLUMNS}
        )

    return False  # Newly added


def modify(instance_name, instance_data):
    """
    Modifies an existing instance in the instances list TSV.

    Args:
        instance_name (str): The name of the instance to modify.
        instance_data (dict): A dictionary of fieldnames and new values to update.

    Raises:
        ValueError: If the instance is not found, or if instance_name conflicts with instance_data["instance_name"].
    """
    # Sanity check: ensure instance_name is consistent
    if "instance_name" in instance_data:
        if instance_data["instance_name"] != instance_name:
            raise ValueError(
                f"Mismatch between argument instance_name ('{instance_name}') "
                f"and instance_data['instance_name'] ('{instance_data['instance_name']}')."
            )
    else:
        instance_data["instance_name"] = instance_name

    path = fileio.path("instances list")

    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        rows = list(reader)
        fieldnames = reader.fieldnames

    modified = False
    for row in rows:
        if row.get("instance_name") == instance_name:
            row.update(instance_data)
            modified = True
            break

    if not modified:
        raise ValueError(f"Instance '{instance_name}' not found in the instances list.")

    # Add debug call chain
    instance_data["debug"] = get_call_chain_str()
    instance_data["debug_cutoff"] = " "

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def make_new_list():
    with open(fileio.path("instances list"), "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=INSTANCES_LIST_COLUMNS, delimiter="\t")
        writer.writeheader()
        writer.writerows([])


def assign_bom_line_numbers():
    bom = []
    for instance in read_instance_rows():
        if instance.get("bom_line_number") == "True":
            if instance.get("mpn") == "":
                raise ValueError(
                    f"You've chosen to add {instance.get('instance_name')} to the bom, but haven't specified an MPN"
                )
            if instance.get("mpn") not in bom:
                bom.append(instance.get("mpn"))

    bom_line_number = 1
    for bom_item in bom:
        for instance in read_instance_rows():
            if instance.get("mpn") == bom_item:
                modify(
                    instance.get("instance_name"), {"bom_line_number": bom_line_number}
                )
        bom_line_number += 1


def add_revhistory_of_imported_part(instance_name, rev_data):
    # Expected rev_data is a dict with keys from REVISION_HISTORY_COLUMNS
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


def instance_names_of_adjacent_ports(target_instance):
    for instance in read_instance_rows():
        if instance.get("instance_name") == target_instance:
            # assign parents to contacts based on the assumption that one of the two adjacent items in the circuit will be a node-item
            if (
                instance.get("circuit_id") == ""
                or instance.get("circuit_id_port") == ""
            ):
                raise ValueError(f"Circuit order unspecified for {target_instance}")

            circuit_id = instance.get("circuit_id")
            circuit_id_port = int(instance.get("circuit_id_port"))

            # find the adjacent port
            prev_port = ""
            next_port = ""

            for instance2 in read_instance_rows():
                if instance2.get("circuit_id") == circuit_id:
                    if int(instance2.get("circuit_id_port")) == circuit_id_port - 1:
                        prev_port = instance2.get("instance_name")
                    if int(instance2.get("circuit_id_port")) == circuit_id_port + 1:
                        next_port = instance2.get("instance_name")

            return prev_port, next_port


def attribute_of(target_instance, attribute):
    for instance in read_instance_rows():
        if instance.get("instance_name") == target_instance:
            return instance.get(attribute)


def instance_in_cluster_with_suffix(cluster, suffix):
    match = None
    for instance in read_instance_rows():
        if instance.get("cluster") == cluster:
            instance_name = instance.get("instance_name", "")
            if instance_name.endswith(suffix):
                if match is not None:
                    raise ValueError(
                        f"We found multiple instances in cluster '{cluster}' with the suffix '{suffix}'."
                    )
                match = instance_name
    return match


def get_call_chain_str():
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


def chmap_to_circuits():
    """
    Convert mapped channels (from channel map) into circuit + signal instances.

    Rules:
        - If exactly two of (from_key, to_key, splice_id) are populated,
          the channel must be mapped into instances.
        - Look up the channel type to determine how many signals it contains.
        - For each involved device/box, find signals in its signals list.
        - Add two instances per signal (with parent = connector instance).
        - Add one instance for the circuit (per net).
        - Add two instances for the mating connectors.

    Sources of data:
        - Channels live in the channel map
        - Channel types are irrelevant here
        - Signals of a channel lives in imported_devices
    """

    circuit_id = 0
    for mapped_channel in system_utils.read_channel_map():
        from_key = (
            mapped_channel.get("from_device_refdes"),
            mapped_channel.get("from_device_channel_id"),
        )
        to_key = (
            mapped_channel.get("to_device_refdes"),
            mapped_channel.get("to_device_channel_id"),
        )
        splice = mapped_channel.get("splice_key")

        # See if a channel is "mapped": either from and to are populated or from and splice are populated, aka two of the three must be populated
        populated = [bool(from_key[0]), bool(to_key[0]), bool(splice)]

        if sum(populated) != 2:
            continue  # if two of the three are populated, this counts as a "mapped channel", otherwise, it's unmapped so skip it

        # ---- Gather signals from involved devices ----
        from_device_refdes, from_channel_id = from_key
        to_device_refdes, to_channel_id = to_key

        # Look up the device MPN from its refdes the bom
        from_device_mfg, from_device_mpn, from_device_rev = (
            system_utils.mpn_of_device_refdes(from_device_refdes)
        )
        to_device_mfg, to_device_mpn, to_device_rev = system_utils.mpn_of_device_refdes(
            to_device_refdes
        )

        # Find the device signals list
        from_device_signals_list_path = os.path.join(
            fileio.dirpath("devices"),
            from_device_refdes,
            f"{from_device_mpn}-{from_device_rev}-signals-list.tsv",
        )
        to_device_signals_list_path = os.path.join(
            fileio.dirpath("devices"),
            to_device_refdes,
            f"{to_device_mpn}-{to_device_rev}-signals-list.tsv",
        )

        # Generate a mating connector name
        from_mating_connector_name = f"X-{from_device_refdes}-{icd.mating_connector_of_channel(from_channel_id, from_device_signals_list_path)}"
        to_mating_connector_name = f"X-{to_device_refdes}-{icd.mating_connector_of_channel(to_channel_id, to_device_signals_list_path)}"

        # Add mating connectors to instances list
        add_unless_exists(
            from_mating_connector_name,
            {
                "net": mapped_channel.get("merged_net"),
                "item_type": "Connector",
                "cluster": from_mating_connector_name,
            },
        )
        add_unless_exists(
            to_mating_connector_name,
            {
                "net": mapped_channel.get("merged_net"),
                "item_type": "Connector",
                "cluster": to_mating_connector_name,
            },
        )

        # only need to cycle through the from channels, because at this point it is assumed that the to channels are compatible and therefore matching
        for signal in icd.signals_of_channel(
            from_channel_id, from_device_signals_list_path
        ):
            add_unless_exists(
                f"{from_device_refdes}-{from_channel_id}-{signal}",
                {
                    "net": mapped_channel.get("merged_net"),
                    "item_type": "Signal",
                    "signal": signal,
                    "parent_instance": from_mating_connector_name,
                    "cluster": from_mating_connector_name,
                    "circuit_id": f"circuit_{circuit_id}",
                },
            )
            add_unless_exists(
                f"{to_device_refdes}-{to_channel_id}-{signal}",
                {
                    "net": mapped_channel.get("merged_net"),
                    "item_type": "Signal",
                    "signal": signal,
                    "parent_instance": to_mating_connector_name,
                    "cluster": to_mating_connector_name,
                    "circuit_id": f"circuit_{circuit_id}",
                },
            )
            add_unless_exists(
                f"{from_device_refdes}-{from_channel_id}-{to_device_refdes}-{to_channel_id}-{signal}",
                {
                    "net": mapped_channel.get("merged_net"),
                    "item_type": "Circuit",
                    "signal": signal,
                    "circuit_id": f"circuit_{circuit_id}",
                    "node_at_end_a": f"{from_device_refdes}-{from_channel_id}-{signal}",
                    "node_at_end_b": f"{to_device_refdes}-{to_channel_id}-{signal}",
                },
            )
            circuit_id += 1
