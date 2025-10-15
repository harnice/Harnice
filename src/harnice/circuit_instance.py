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
