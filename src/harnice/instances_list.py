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


def add_connector_contact_nodes_and_circuits():
    with open(fileio.path("circuits list"), newline="", encoding="utf-8") as f:
        circuits_list = list(csv.DictReader(f, delimiter="\t"))

    for circuit in circuits_list:
        #add connectors and contacts

        from_connector_key = f"{circuit.get('net_from_refdes')}.{circuit.get('net_from_connector_name')}"
        from_connector_node = f"{from_connector_key}.node"

        from_contact_key = f"{circuit.get('net_from_refdes')}.{circuit.get('net_from_connector_name')}.{circuit.get('net_from_contact')}"
        from_contact_node = f"{from_contact_key}.node"

        to_connector_key = f"{circuit.get('net_to_refdes')}.{circuit.get('net_to_connector_name')}"
        to_connector_node = f"{to_connector_key}.node"

        to_contact_key = f"{circuit.get('net_to_refdes')}.{circuit.get('net_to_connector_name')}.{circuit.get('net_to_contact')}"
        to_contact_node = f"{to_contact_key}.node"

        add_unless_exists(from_connector_node, {
            "net": circuit.get('net'),
            "item_type": "Node",
            "location_is_node_or_segment": "Node",
            "cluster": from_connector_key
        })
        add_unless_exists(from_contact_node, {
            "net": circuit.get('net'),
            "item_type": "Node",
            "parent_instance": from_connector_node,
            "location_is_node_or_segment": "Node",
            "cluster": from_connector_key
        })

        add_unless_exists(to_connector_node, {
            "net": circuit.get('net'),
            "item_type": "Node",
            "location_is_node_or_segment": "Node",
            "cluster": to_connector_key
        })
        add_unless_exists(to_contact_node, {
            "net": circuit.get('net'),
            "item_type": "Node",
            "parent_instance": to_connector_node,
            "location_is_node_or_segment": "Node",
            "cluster": to_connector_key
        })

        #add circuit
        circuit_name = f"circuit-{circuit.get('circuit_id')}"
        circuit_data = {
            "net": circuit.get("net"),
            "item_type": "Circuit",
            "circuit_id": circuit.get("circuit_id"),
            "node_at_end_a": from_contact_node,
            "node_at_end_b": to_contact_node
        }

        add_unless_exists(circuit_name, circuit_data)