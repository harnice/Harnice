import re  # for regex matching like re.match and re.fullmatch
import yaml
import os
from harnice import instances_list, fileio, circuit_instance

build_macro_mpn = "import_harnice_esch"


def path(target_value):
    if target_value == "harness yaml":
        return os.path.join(os.getcwd(), f"{fileio.partnumber('pn-rev')}-esch.yaml")
    else:
        raise KeyError(
            f"Filename {target_value} not found in {build_macro_mpn} file tree"
        )


# =============== CREATE BASE INSTANCES FROM ESCH #===============
# Load the YAML file once and parse it
with open(path("harness yaml"), "r", encoding="utf-8") as f:
    harness_yaml = yaml.safe_load(f)

# Iterate over the circuits and their associated ports
for circuit_id, ports in harness_yaml.items():
    instances_list.new_instance(circuit_id, {"item_type": "Circuit"})
    port_counter = 0
    contact_counter = 0  # Automatically number contacts like contact1, contact2, etc.

    # Go through each port in this circuit
    # Port label is the port, value is either a string or a dictionary
    for port_label, value in ports.items():
        if port_label == "contact":
            # Automatically name the contact with the circuit name and a number
            instance_name = f"{circuit_id}.contact{contact_counter}"
            contact_counter += 1

            # Add this contact to the system with its part number (mpn)

            if value == "TXPA20":
                lib_repo = "https://github.com/kenyonshutt/harnice-library-public"

            instances_list.new_instance(
                instance_name,
                {
                    "item_type": "Contact",
                    "bom_line_number": True,
                    "mpn": value,
                    "lib_repo": lib_repo,
                    "location_type": "Node",
                    "circuit_id": circuit_id,
                    "circuit_port_number": port_counter,
                },
            )

        else:
            # Check the label of the port to decide what kind of part it is.
            # By default, anything starting with "X" or "W" is treated as a Connector.
            if re.match(r"X[^.]+", port_label):
                instances_list.new_instance(
                    port_label,
                    {
                        "item_type": "Connector",
                        "connector_group": port_label,
                        "location_type": "Node",
                    },
                )
                instances_list.new_instance(
                    f"{port_label}.node",
                    {
                        "item_type": "Node",
                        "connector_group": port_label,
                        "location_type": "Node",
                        "parent_csys_instance_name": "origin",
                        "parent_csys_outputcsys_name": "origin",
                    },
                )
            elif re.match(r"C[^.]+", port_label):
                instances_list.new_instance(
                    port_label,
                    {"item_type": "Cable", "location_type": "Segment"},
                )
            else:
                raise ValueError(f"Please define item {port_label}!")

            # If the port contains more detailed information (like cavity or conductor),
            # the value will be a dictionary with extra fields
            if type(value) is dict:
                for subkey, subval in value.items():
                    # If the field is "cavity", add a cavity under this connector
                    if subkey == "cavity":
                        instance_name = f"{port_label}.cavity{subval}"
                        instances_list.new_instance(
                            instance_name,
                            {
                                "print_name": subval,
                                "item_type": "Connector cavity",
                                "parent_instance": port_label,
                                "connector_group": port_label,
                                "location_type": "Node",
                                "circuit_id": circuit_id,
                                "circuit_port_number": port_counter,
                            },
                        )

                    # If the field is "conductor", add a conductor under this wire
                    elif subkey == "conductor":
                        instance_name = f"{port_label}.conductor{subval}"
                        instances_list.new_instance(
                            instance_name,
                            {
                                "print_name": subval,
                                "item_type": "Conductor",
                                "parent_instance": port_label,
                                "location_type": "Segment",
                                "circuit_id": circuit_id,
                                "circuit_port_number": port_counter,
                            },
                        )

                    # If the field is something else (like "shield" or "tag"), we still include it
                    else:
                        instance_name = f"{port_label}.{subkey}{subval}"
                        instances_list.add_instance_unless_exists(instance_name, {})

            else:
                # If the port is just a single value (not a dictionary), we still add it as a sub-instance
                instance_name = f"{port_label}.{value}"
                instances_list.add_instance_unless_exists(instance_name, {})

        port_counter += 1


# ================ ASSIGN MPNS TO CONNECTORS #===============
for instance in instances_list.read_instance_rows():
    instance_name = instance.get("instance_name")
    if instance.get("item_type") == "Connector":
        if instance_name == "X1":
            instances_list.modify(
                instance_name,
                {
                    "bom_line_number": "True",
                    "mpn": "D38999_26ZB98PN",
                    "lib_repo": "https://github.com/kenyonshutt/harnice-library-public",
                },
            )
        else:
            instances_list.modify(
                instance_name,
                {
                    "bom_line_number": "True",
                    "mpn": "D38999_26ZA98PN",
                    "lib_repo": "https://github.com/kenyonshutt/harnice-library-public",
                },
            )


# ================ ASSIGN PRINT NAMES TO CONNECTORS #===============
for instance in instances_list.read_instance_rows():
    instance_name = instance.get("instance_name")
    if instance_name == "X1":
        instances_list.modify(instance_name, {"print_name": "P1"})
    elif instance_name == "X2":
        instances_list.modify(instance_name, {"print_name": "P2"})
    elif instance_name == "X3":
        instances_list.modify(instance_name, {"print_name": "P3"})
    elif instance_name == "X4":
        instances_list.modify(instance_name, {"print_name": "J1"})
    elif instance_name == "X500":
        instances_list.modify(instance_name, {"print_name": "J2"})
    elif instance.get("item_type") == "Connector":
        raise ValueError(
            f"Connector {instance.get('instance_name')} defined but does not have a print name assigned."
        )


# ================ ASSIGN BACKSHELLS AND ACCESSORIES TO CONNECTORS #===============
for instance in instances_list.read_instance_rows():
    instance_name = instance.get("instance_name")
    if instance.get("item_type") == "Connector":
        mpn = instance.get("mpn")
        if re.fullmatch(r"D38999_26ZA.+", mpn):
            if instance.get("print_name") not in ["P3", "J1"]:
                instances_list.new_instance(
                    f"{instance_name}.bs",
                    {
                        "mpn": "M85049-88_9Z03",
                        "print_name": f"{instances_list.attribute_of(instance_name, 'print_name')}.bs",
                        "bom_line_number": "True",
                        "lib_repo": "https://github.com/kenyonshutt/harnice-library-public",
                        "item_type": "Backshell",
                        "parent_instance": instance.get("instance_name"),
                        "connector_group": instance_name,
                        "location_type": "Node",
                    },
                )


# =============== ASSIGN PARENTS TO WEIRD PARTS LIKE CONTACTS #===============
for instance in instances_list.read_instance_rows():
    if instance.get("item_type") == "Contact":
        instance_name = instance.get("instance_name")
        prev_port, next_port = circuit_instance.instance_names_of_adjacent_ports(
            instance_name
        )
        prev_port_location_type = instances_list.attribute_of(
            prev_port, "location_type"
        )
        next_port_location_type = instances_list.attribute_of(
            next_port, "location_type"
        )
        if prev_port_location_type == "Node" and next_port_location_type == "Segment":
            instances_list.modify(
                instance_name,
                {
                    "parent_instance": prev_port,
                    "connector_group": instances_list.attribute_of(
                        prev_port, "connector_group"
                    ),
                },
            )
        elif prev_port_location_type == "Segment" and next_port_location_type == "Node":
            instances_list.modify(
                instance_name,
                {
                    "parent_instance": next_port,
                    "connector_group": instances_list.attribute_of(
                        prev_port, "connector_group"
                    ),
                },
            )
        else:
            raise ValueError(
                f"Because adjacent ports are both port-based or both segment-based, I don't know what parent to assign to {instance_name}"
            )


# ================ ASSIGN MPNS TO CABLES #===============
# TODO: UPDATE THIS PER https://github.com/kenyonshutt/harnice/issues/69
for instance in instances_list.read_instance_rows():
    if instance.get("item_type") == "Cable":
        instances_list.modify(
            instance.get("instance_name"), {"mpn": "test", "bom_line_number": "True"}
        )
