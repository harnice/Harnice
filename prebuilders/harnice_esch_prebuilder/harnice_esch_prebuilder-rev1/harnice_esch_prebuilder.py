import re  # for regex matching like re.match and re.fullmatch
import yaml
import os
from harnice import instances_list, fileio  # assuming your project structure provides these

prebuilder_mpn = "harnice_esch_prebuilder"

def path(target_value):
    if target_value == "harness yaml":
        return os.path.join(os.getcwd(), f"{fileio.partnumber("pn-rev")}-esch.yaml")
    else:
        raise KeyError(f"Filename {target_value} not found in {prebuilder_mpn} file tree")

#=============== CREATE BASE INSTANCES FROM ESCH #===============
# Load the YAML file once and parse it
with open(path("harness yaml"), "r", encoding="utf-8") as f:
    harness_yaml = yaml.safe_load(f)

# Iterate over the circuits and their associated ports
for circuit_name, ports in harness_yaml.items():
    instances_list.add(circuit_name, {
        "item_type": "Circuit"
    })
    port_counter = 0
    contact_counter = 0  # Automatically number contacts like contact1, contact2, etc.

    # Go through each port in this circuit
    # Port label is the port, value is either a string or a dictionary
    for port_label, value in ports.items():

        if port_label == "contact":
            # Automatically name the contact with the circuit name and a number
            instance_name = f"{circuit_name}.contact{contact_counter}"
            contact_counter += 1

            # Add this contact to the system with its part number (mpn)

            if value == "TXPA20":
                supplier = "public"

            instances_list.add_unless_exists(instance_name, {
                "item_type": "Contact",
                "bom_line_number": True,
                "mpn": value,
                "supplier": supplier,
                "location_is_node_or_segment": "Node",
                'circuit_id': circuit_name,
                'circuit_id_port': port_counter
            })

        else:
            # Check the label of the port to decide what kind of part it is.
            # By default, anything starting with "X" or "W" is treated as a Connector.
            if re.match(r"X[^.]+", port_label):
                instances_list.add_unless_exists(port_label,{
                    "item_type": "Connector",
                    "cluster": port_label,
                    "location_is_node_or_segment": "Node"
                })
                instances_list.add_unless_exists(f"{port_label}.node",{
                    "item_type": "Node",
                    "cluster": port_label,
                    "location_is_node_or_segment": "Node",
                    "parent_csys_instance_name": "origin",
                    "parent_csys_outputcsys_name": "origin"
                })
            elif re.match(r"C[^.]+", port_label):
                instances_list.add_unless_exists(port_label,{
                    "item_type": "Cable",
                    "location_is_node_or_segment": "Segment"
                })
            else:
                raise ValueError(f"Please define item {port_label}!")

            # If the port contains more detailed information (like cavity or conductor),
            # the value will be a dictionary with extra fields
            if type(value) is dict:
                for subkey, subval in value.items():

                    # If the field is "cavity", add a cavity under this connector
                    if subkey == "cavity":
                        instance_name = f"{port_label}.cavity{subval}"
                        instances_list.add_unless_exists(instance_name,{
                            "print_name": subval,
                            "item_type": "Connector cavity",
                            "parent_instance": port_label,
                            "cluster": port_label,
                            "location_is_node_or_segment": "Node",
                            'circuit_id': circuit_name,
                            'circuit_id_port': port_counter
                        })

                    # If the field is "conductor", add a conductor under this wire
                    elif subkey == "conductor":
                        instance_name = f"{port_label}.conductor{subval}"
                        instances_list.add_unless_exists(instance_name,{
                            "print_name": subval,
                            "item_type": "Conductor",
                            "parent_instance": port_label,
                            "location_is_node_or_segment": "Segment",
                            'circuit_id': circuit_name,
                            'circuit_id_port': port_counter
                        })

                    # If the field is something else (like "shield" or "tag"), we still include it
                    else:
                        instance_name = f"{port_label}.{subkey}{subval}"
                        instances_list.add_instance_unless_exists(instance_name,{})

            else:
                # If the port is just a single value (not a dictionary), we still add it as a sub-instance
                instance_name = f"{port_label}.{value}"
                instances_list.add_instance_unless_exists(instance_name,{})
        
        port_counter += 1


#================ ASSIGN MPNS TO CONNECTORS #===============
for instance in instances_list.read_instance_rows():
    instance_name = instance.get("instance_name")
    if instance.get("item_type") == "Connector":
        if instance_name == "X1":
            instances_list.modify(instance_name,{
                "bom_line_number": "True",
                "mpn": "D38999_26ZB98PN",
                "supplier": "public"
            })
        else:
            instances_list.modify(instance_name,{
                "bom_line_number": "True",
                "mpn": "D38999_26ZA98PN",
                "supplier": "public"
            })


#================ ASSIGN PRINT NAMES TO CONNECTORS #===============
for instance in instances_list.read_instance_rows():
    instance_name = instance.get("instance_name")
    if instance_name == "X1":
        instances_list.modify(instance_name,{
            "print_name": "P1"
        })
    elif instance_name == "X2":
        instances_list.modify(instance_name,{
            "print_name": "P2"
        })
    elif instance_name == "X3":
        instances_list.modify(instance_name,{
            "print_name": "P3"
        })
    elif instance_name == "X4":
        instances_list.modify(instance_name,{
            "print_name": "J1"
        })
    elif instance_name == "X500":
        instances_list.modify(instance_name,{
            "print_name": "J2"
        })
    elif instance.get("item_type") == "Connector":
        raise ValueError(f"Connector {instance.get("instance_name")} defined but does not have a print name assigned.")


#================ ASSIGN BACKSHELLS AND ACCESSORIES TO CONNECTORS #===============
for instance in instances_list.read_instance_rows():
    instance_name = instance.get("instance_name")
    if instance.get("item_type") == "Connector":
        mpn = instance.get("mpn")
        if re.fullmatch(r"D38999_26ZA.+", mpn):
            if instance.get("print_name") not in ["P3", "J1"]:
                instances_list.add(f"{instance_name}.bs",{
                    "mpn": "M85049-88_9Z03",
                    "print_name": f"{instances_list.attribute_of(instance_name, "print_name")}.bs",
                    "bom_line_number": "True",
                    "supplier": "public",
                    "item_type": "Backshell",
                    "parent_instance": instance.get("instance_name"),
                    "cluster": instance_name,
                    "location_is_node_or_segment": "Node"
                })


#=============== ASSIGN PARENTS TO WEIRD PARTS LIKE CONTACTS #===============
for instance in instances_list.read_instance_rows():
    if instance.get("item_type") == "Contact":
        instance_name = instance.get("instance_name")
        prev_port, next_port = instances_list.instance_names_of_adjacent_ports(instance_name)
        prev_port_location_is_node_or_segment = instances_list.attribute_of(prev_port, "location_is_node_or_segment")
        next_port_location_is_node_or_segment = instances_list.attribute_of(next_port, "location_is_node_or_segment")
        if prev_port_location_is_node_or_segment == "Node" and next_port_location_is_node_or_segment == "Segment":
            instances_list.modify(instance_name,{
                "parent_instance": prev_port,
                "cluster": instances_list.attribute_of(prev_port, "cluster")
            })
        elif prev_port_location_is_node_or_segment == "Segment" and next_port_location_is_node_or_segment == "Node":
            instances_list.modify(instance_name,{
                "parent_instance": next_port,
                "cluster": instances_list.attribute_of(prev_port, "cluster")
            })
        else:
            raise ValueError(f"Because adjacent ports are both port-based or both segment-based, I don't know what parent to assign to {instance_name}")


#================ ASSIGN MPNS TO CABLES #===============
#TODO: UPDATE THIS PER https://github.com/kenyonshutt/harnice/issues/69
for instance in instances_list.read_instance_rows():
    if instance.get("item_type") == "Cable":
        instances_list.modify(instance.get("instance_name"),{
            "mpn": "test",
            "bom_line_number": "True"
        })