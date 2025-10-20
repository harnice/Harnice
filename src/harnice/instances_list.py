import csv
import os
import inspect
from threading import Lock
from harnice import component_library, fileio, signals_list

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
    "lib_latest_rev",
    "lib_rev_used_here",
    "lib_status",
    "lib_datemodified",
    "lib_datereleased",
    "lib_drawnby",
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
    "this_channel_from_channel_type_id",
    "this_channel_to_channel_type_id",
    "signal_of_channel_type",
    "debug",
    "debug_cutoff",
]


def read_instance_rows():
    with open(fileio.path("instances list"), newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter="\t"))


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

    if any(row.get("instance_name") == instance_name for row in read_instance_rows()):
        if not ignore_duplicates:
            raise ValueError(
                f"An instance with the name '{instance_name}' already exists"
            )
        else:
            return -1

    if fileio.get_net() and fileio.product_type == "harness":
        instance_data["net"] = fileio.get_net()

    # Add debug call chain
    instance_data["debug"] = get_call_chain_str()
    instance_data["debug_cutoff"] = " "

    # add argumet to data added
    instance_data["instance_name"] = instance_name

    with open(fileio.path("instances list"), "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=INSTANCES_LIST_COLUMNS, delimiter="\t")
        writer.writerow(
            {key: instance_data.get(key, "") for key in INSTANCES_LIST_COLUMNS}
        )


_instances_lock = Lock()


def modify(instance_name, instance_data):
    with _instances_lock:
        path = fileio.path("instances list")
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter="\t")
            rows = list(reader)
            fieldnames = reader.fieldnames

        for row in rows:
            if row.get("instance_name") == instance_name:
                row.update(instance_data)
                break
        else:
            raise ValueError(f"Instance '{instance_name}' not found")

        tmp = path + ".tmp"
        with open(tmp, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")
            writer.writeheader()
            writer.writerows(rows)
            f.flush()
            os.fsync(f.fileno())

        os.replace(tmp, path)


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


def attribute_of(target_instance, attribute):
    for instance in read_instance_rows():
        if instance.get("instance_name") == target_instance:
            return instance.get(attribute)


def instance_in_connector_group_with_item_type(connector_group, item_type):
    if connector_group in ["", None]:
        raise ValueError("Connector group is blank")
    if item_type in ["", None]:
        raise ValueError("Suffix is blank")
    match = 0
    output = None
    for instance in read_instance_rows():
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


def add_connector_contact_nodes_channels_and_circuits():
    with open(fileio.path("system connector list"), newline="", encoding="utf-8") as f:
        connectors_list = list(csv.DictReader(f, delimiter="\t"))

    with open(fileio.path("circuits list"), newline="", encoding="utf-8") as f:
        circuits_list = list(csv.DictReader(f, delimiter="\t"))

    for circuit in circuits_list:
        from_connector_key = (
            f"{circuit.get('net_from_refdes')}.{circuit.get('net_from_connector_name')}"
        )
        from_cavity = f"{circuit.get('net_from_refdes')}.{circuit.get('net_from_connector_name')}.{circuit.get('net_from_cavity')}"
        
        from_connector_mpn = ""
        for connector in connectors_list:
            if connector.get("device_refdes") == circuit.get("net_from_refdes") and connector.get("connector") == circuit.get("net_from_connector_name"):
                from_connector_mpn = connector.get("connector_mpn")
                break

        #from connector node
        new_instance(
            f"{from_connector_key}.node",
            {
                "net": circuit.get("net"),
                "item_type": "Node",
                "location_is_node_or_segment": "Node",
                "connector_group": from_connector_key,
            },
            ignore_duplicates=True,
        )

        #from connector
        new_instance(
            f"{from_connector_key}.conn",
            {
                "net": circuit.get("net"),
                "item_type": "Connector",
                "location_is_node_or_segment": "Node",
                "connector_group": from_connector_key,
                "this_instance_mating_device_refdes": circuit.get("net_from_refdes"),
                "this_instance_mating_device_connector": circuit.get("net_from_connector_name"),
                "this_instance_mating_device_connector_mpn": from_connector_mpn,
            },
            ignore_duplicates=True,
        )

        #from connector cavity
        new_instance(
            from_cavity,
            {
                "net": circuit.get("net"),
                "item_type": "Connector cavity",
                "parent_instance": f"{from_connector_key}.conn", #from connector instance
                "location_is_node_or_segment": "Node",
                "connector_group": from_connector_key,
                "circuit_id": circuit.get("circuit_id"),
                "circuit_port_number": 0,
            },
            ignore_duplicates=True,
        )

        to_connector_key = (
            f"{circuit.get('net_to_refdes')}.{circuit.get('net_to_connector_name')}"
        )
        to_cavity = f"{circuit.get('net_to_refdes')}.{circuit.get('net_to_connector_name')}.{circuit.get('net_to_cavity')}"

        to_connector_mpn = ""
        for connector in connectors_list:
            if connector.get("device_refdes") == circuit.get("net_to_refdes") and connector.get("connector") == circuit.get("net_to_connector_name"):
                to_connector_mpn = connector.get("connector_mpn")
                break

        #to connector node
        new_instance(
            f"{to_connector_key}.node",
            {
                "net": circuit.get("net"),
                "item_type": "Node",
                "location_is_node_or_segment": "Node",
                "connector_group": to_connector_key,
            },
            ignore_duplicates=True,
        )

        #to connector
        new_instance(
            f"{to_connector_key}.conn",
            {
                "net": circuit.get("net"),
                "item_type": "Connector",
                "location_is_node_or_segment": "Node",
                "connector_group": to_connector_key,
                "this_instance_mating_device_refdes": circuit.get("net_from_refdes"),
                "this_instance_mating_device_connector": circuit.get("net_from_connector_name"),
                "this_instance_mating_device_connector_mpn": to_connector_mpn,
            },
            ignore_duplicates=True,
        )

        #to connector cavity
        new_instance(
            to_cavity,
            {
                "net": circuit.get("net"),
                "item_type": "Connector cavity",
                "parent_instance": f"{to_connector_key}.conn", #to connector instance
                "location_is_node_or_segment": "Node",
                "connector_group": to_connector_key,
                "circuit_id": circuit.get("circuit_id"),
                "circuit_port_number": 1,
            },
            ignore_duplicates=True,
        )

        # add circuit
        new_instance(
            f"circuit-{circuit.get('circuit_id')}",
            {
                "net": circuit.get("net"),
                "item_type": "Circuit",
                "channel_group": f"channel-{circuit.get('from_side_device_refdes')}.{circuit.get('from_side_device_chname')}-{circuit.get('to_side_device_refdes')}.{circuit.get('to_side_device_chname')}",
                "circuit_id": circuit.get("circuit_id"),
                "node_at_end_a": from_cavity,
                "node_at_end_b": to_cavity,
                "this_net_from_device_refdes": circuit.get("net_from_refdes"),
                "this_net_from_device_channel_id": circuit.get("net_from_channel_id"),
                "this_net_from_device_connector_name": circuit.get(
                    "net_from_connector_name"
                ),
                "this_net_to_device_refdes": circuit.get("net_to_refdes"),
                "this_net_to_device_channel_id": circuit.get("net_to_channel_id"),
                "this_net_to_device_connector_name": circuit.get(
                    "net_to_connector_name"
                ),
                "this_channel_from_device_refdes": circuit.get(
                    "from_side_device_refdes"
                ),
                "this_channel_from_device_channel_id": circuit.get(
                    "from_side_device_chname"
                ),
                "this_channel_to_device_refdes": circuit.get("to_side_device_refdes"),
                "this_channel_to_device_channel_id": circuit.get(
                    "to_side_device_chname"
                ),
                "this_channel_from_channel_type_id": circuit.get(
                    "from_channel_type_id"
                ),
                "this_channel_to_channel_type_id": circuit.get("to_channel_type_id"),
                "signal_of_channel_type": circuit.get("signal"),
            },
            ignore_duplicates=True,
        )

        new_instance(
            f"channel-{circuit.get('from_side_device_refdes')}.{circuit.get('from_side_device_chname')}-{circuit.get('to_side_device_refdes')}.{circuit.get('to_side_device_chname')}",
            {
                "net": circuit.get("net"),
                "item_type": "Channel",
                "channel_group": f"channel-{circuit.get('from_side_device_refdes')}.{circuit.get('from_side_device_chname')}-{circuit.get('to_side_device_refdes')}.{circuit.get('to_side_device_chname')}",
                "this_net_from_device_refdes": circuit.get("net_from_refdes"),
                "this_net_from_device_channel_id": circuit.get("net_from_channel_id"),
                "this_net_from_device_connector_name": circuit.get(
                    "net_from_connector_name"
                ),
                "this_net_to_device_refdes": circuit.get("net_to_refdes"),
                "this_net_to_device_channel_id": circuit.get("net_to_channel_id"),
                "this_net_to_device_connector_name": circuit.get(
                    "net_to_connector_name"
                ),
                "this_channel_from_device_refdes": circuit.get(
                    "from_side_device_refdes"
                ),
                "this_channel_from_device_channel_id": circuit.get(
                    "from_side_device_chname"
                ),
                "this_channel_to_device_refdes": circuit.get("to_side_device_refdes"),
                "this_channel_to_device_channel_id": circuit.get(
                    "to_side_device_chname"
                ),
                "this_channel_from_channel_type_id": circuit.get(
                    "from_channel_type_id"
                ),
                "this_channel_to_channel_type_id": circuit.get("to_channel_type_id"),
            },
            ignore_duplicates=True,
        )

    with open(fileio.path("system connector list"), newline="", encoding="utf-8") as f:
        connector_list = list(csv.DictReader(f, delimiter="\t"))

    for connector in connector_list:
        try:
            modify(
                f"{connector.get('device_refdes')}.{connector.get('connector')}.conn",
                {
                    "mating_device_refdes": connector.get("device_refdes"),
                    "mating_device_connector": connector.get("connector"),
                    "mating_device_connector_mpn": connector.get("connector_mpn"),
                },
            )
        except ValueError:
            pass

def assign_cable_conductor(
    cable_instance_name,  # unique identifier for the cable in your project
    cable_conductor_id,  # (container, identifier) tuple identifying the conductor in the cable being imported
    conductor_instance,  # instance name of the conductor in your project
    library_info,  # dict containing library info: {lib_repo, mpn, lib_subpath, used_rev, item_name}
):
    instances = read_instance_rows()

    # --- Check if cable is already imported ---
    already_imported = any(
        inst.get("instance_name") == cable_instance_name for inst in instances
    )

    # --- Import from library if not already imported ---
    if not already_imported:
        lib_subpath = library_info.get("lib_subpath", "")
        used_rev = library_info.get("used_rev", "")

        destination_directory = os.path.join(
            fileio.dirpath("imported_instances"), cable_instance_name
        )

        os.makedirs(destination_directory, exist_ok=True)

        component_library.pull_item_from_library(
            lib_repo=library_info.get("lib_repo"),
            product="cables",
            mpn=library_info.get("mpn"),
            destination_directory=destination_directory,
            lib_subpath=lib_subpath,
            used_rev=used_rev,
            item_name=cable_instance_name,
        )

        new_instance(
            cable_instance_name,
            {
                "item_type": "Cable",
                "location_is_node_or_segment": "Segment",
                "cable_group": cable_instance_name,
            },
        )

    # --- Make sure conductor of cable has not been assigned yet
    for instance in instances:
        if instance.get("cable_group") == cable_instance_name:
            if instance.get("cable_container") == cable_conductor_id[0]:
                if instance.get("cable_identifier") == cable_conductor_id[1]:
                    raise ValueError(
                        f"Conductor {cable_conductor_id} has already been assigned to {instance.get('instance_name')}"
                    )

    # --- Make sure conductor instance has not already been assigned to a cable
    for instance in instances:
        if instance.get("instance_name") == conductor_instance:
            if (
                instance.get("cable_group") not in ["", None]
                or instance.get("cable_container") not in ["", None]
                or instance.get("cable_identifier") not in ["", None]
            ):
                raise ValueError(
                    f"Conductor '{conductor_instance}' has already been assigned "
                    f"to '{instance.get('cable_identifier')}' of cable '{instance.get('cable_group')}'"
                )

    # --- assign conductor
    for instance in instances:
        if instance.get("instance_name") == conductor_instance:
            modify(
                conductor_instance,
                {
                    "parent_instance": cable_instance_name,
                    "cable_group": cable_instance_name,
                    "cable_container": cable_conductor_id[0],
                    "cable_identifier": cable_conductor_id[1],
                },
            )
            break
