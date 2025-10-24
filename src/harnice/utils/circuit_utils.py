import os
from harnice import fileio
from harnice.lists import instances_list
from harnice.utils import library_utils


def end_ports_of_circuit(circuit_id):
    try:
        int(circuit_id)
    except ValueError:
        raise ValueError(f"Pass an integer circuit_id, not '{circuit_id}'")
    zero_port = ""
    max_port = ""
    for instance in fileio.read_tsv("instances list"):
        if instance.get("circuit_id") == circuit_id:
            if instance.get("circuit_port_number") == 0:
                zero_port = instance.get("instance_name")
            if instance.get("circuit_port_number") == max_port_number_in_circuit(
                circuit_id
            ):
                max_port = instance.get("instance_name")
    return zero_port, max_port


def max_port_number_in_circuit(circuit_id):
    max_port_number = 0
    for instance in fileio.read_tsv("instances list"):
        if instance.get("circuit_id") == circuit_id:
            if instance.get("circuit_port_number") == "":
                if instance.get("item_type") == "Circuit":
                    continue
                raise ValueError(
                    f"Circuit port number is blank for {instance.get('instance_name')}"
                )
            max_port_number = max(
                max_port_number, int(instance.get("circuit_port_number"))
            )
    return max_port_number


def squeeze_instance_between_ports_in_circuit(
    instance_name, circuit_id, new_circuit_port_number
):
    for instance in fileio.read_tsv("instances list"):
        if instance.get("circuit_id") == circuit_id:
            if instance.get("item_type") == "Circuit":
                continue
            old_port_number = instance.get("circuit_port_number")
            if int(instance.get("circuit_port_number")) < new_circuit_port_number:
                continue
            else:
                instances_list.modify(
                    instance.get("instance_name"),
                    {"circuit_port_number": int(old_port_number) + 1},
                )

        if instance.get("instance_name") == instance_name:
            instances_list.modify(
                instance_name,
                {
                    "circuit_id": circuit_id,
                    "circuit_port_number": new_circuit_port_number,
                },
            )


def instances_of_circuit(circuit_id):
    instances = []
    for instance in fileio.read_tsv("instances list"):
        if instance.get("circuit_id") == circuit_id:
            if instance.get("item_type") == "Circuit":
                continue
            instances.append(instance)

    # sort numerically by circuit_port_number, treating missing as large number
    instances.sort(key=lambda x: int(x.get("circuit_port_number") or 999999))

    return instances


def instance_of_circuit_port_number(circuit_id, circuit_port_number):
    if circuit_id in ["", None]:
        raise ValueError("Circuit ID is blank")
    if circuit_port_number in ["", None]:
        raise ValueError("Circuit port number is blank")

    for instance in fileio.read_tsv("instances list"):
        if instance.get("circuit_id").strip() == str(circuit_id).strip():
            if (
                instance.get("circuit_port_number").strip()
                == str(circuit_port_number).strip()
            ):
                return instance.get("instance_name")

    raise ValueError(
        f"No instance found for circuit {circuit_id} and port number {circuit_port_number}"
    )


def circuit_instance_of_instance(instance_name):
    circuit_instance_name = ""
    instance_rows = fileio.read_tsv("instances list")
    for instance in instance_rows:
        if instance.get("instance_name") == instance_name:
            circuit_instance_name = instance.get("circuit_id")
            break
    for instance in instance_rows:
        if instance.get("circuit_id") == circuit_instance_name:
            if instance.get("instance_name") == instance_name:
                return instance
    raise ValueError(
        f"Circuit instance {circuit_instance_name} of instance {instance_name} not found"
    )


def assign_cable_conductor(
    cable_instance_name,  # unique identifier for the cable in your project
    cable_conductor_id,  # (container, identifier) tuple identifying the conductor in the cable being imported
    conductor_instance,  # instance name of the conductor in your project
    library_info,  # dict containing library info: {lib_repo, mpn, lib_subpath, used_rev, item_name}
):
    instances = fileio.read_tsv("instances list")

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

        library_utils.pull_instance({
            "lib_repo": library_info.get("lib_repo"),
            "item_type": "Cable",
            "mpn": library_info.get("mpn"),
            "instance_name": cable_instance_name,
        })

        instances_list.new_instance(
            cable_instance_name,
            {
                "item_type": "Cable",
                "location_type": "Segment",
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
            instances_list.modify(
                conductor_instance,
                {
                    "parent_instance": cable_instance_name,
                    "cable_group": cable_instance_name,
                    "cable_container": cable_conductor_id[0],
                    "cable_identifier": cable_conductor_id[1],
                },
            )
            break
