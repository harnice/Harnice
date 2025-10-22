from harnice import fileio
from harnice.lists import instances_list


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


def of_instance(instance_name):
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
