from harnice import instances_list


def instance_names_of_adjacent_ports(target_instance):
    for instance in instances_list.read_instance_rows():
        if instance.get("instance_name") == target_instance:
            # assign parents to contacts based on the assumption that one of the two adjacent items in the circuit will be a node-item
            if (
                instance.get("circuit_id") == ""
                or instance.get("circuit_port_number") == ""
            ):
                raise ValueError(f"Circuit order unspecified for {target_instance}")

            circuit_id = instance.get("circuit_id")
            circuit_port_number = int(instance.get("circuit_port_number"))

            # find the adjacent port
            prev_port = ""
            next_port = ""

            for instance2 in instances_list.read_instance_rows():
                if instance2.get("circuit_id") == circuit_id:
                    if (
                        int(instance2.get("circuit_port_number"))
                        == circuit_port_number - 1
                    ):
                        prev_port = instance2.get("instance_name")
                    if (
                        int(instance2.get("circuit_port_number"))
                        == circuit_port_number + 1
                    ):
                        next_port = instance2.get("instance_name")

            return prev_port, next_port


def end_ports_of_circuit(circuit_id):
    zero_port = ""
    max_port = ""
    for instance in instances_list.read_instance_rows():
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
    for instance in instances_list.read_instance_rows():
        if instance.get("circuit_id") == circuit_id:
            max_port_number = max(
                max_port_number, int(instance.get("circuit_port_number"))
            )
    return max_port_number


def squeeze_instance_between_ports_in_circuit(
    instance_name, circuit_id, new_circuit_port_number
):
    for instance in instances_list.read_instance_rows():
        if instance.get("circuit_id") == circuit_id:
            old_port_number = instance.get("circuit_port_number")
            if instance.get("circuit_port_number") < new_circuit_port_number:
                continue
            else:
                instances_list.modify(
                    instance.get("instance_name"),
                    {"circuit_port_number": old_port_number + 1},
                )

        if instance.get("instance_name") == instance_name:
            instances_list.modify(
                instance_name,
                {
                    "circuit_id": circuit_id,
                    "circuit_port_number": new_circuit_port_number,
                },
            )
