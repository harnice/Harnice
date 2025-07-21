#=============== MAKE A WIRELIST #===============
wirelist.newlist(
    [
        {"name": "Circuit_name", "fill": "black", "font": "white"},
        {"name": "Length", "fill": "black", "font": "white"},
        {"name": "Cable", "fill": "black", "font": "white"},
        {"name": "Conductor_identifier", "fill": "black", "font": "white"},

        {"name": "From_connector", "fill": "green", "font": "white"},
        {"name": "From_connector_cavity", "fill": "green", "font": "white"},
        {"name": "From_special_contact", "fill": "green", "font": "white"},

        {"name": "To_special_contact", "fill": "red", "font": "white"},
        {"name": "To_connector", "fill": "red", "font": "white"},
        {"name": "To_connector_cavity", "fill": "red", "font": "white"}
    ]
)

# search through all the circuits in the instances list
for instance in instances_list.read_instance_rows():
    length = ""
    cable = ""
    conductor_identifier = ""
    from_connector = ""
    from_connector_cavity = ""
    from_special_contact = ""
    to_special_contact = ""
    to_connector = ""
    to_connector_cavity = ""

    if instance.get("item_type") == "Circuit":
        circuit_name = instance.get("instance_name")

        # look for "From" and "To" connectors and cavities by cavity
        connector_cavity_counter = 0
        for instance3 in instances_list.read_instance_rows():
            if instance3.get("circuit_id") == circuit_name:
                if instance3.get("item_type") == "Connector cavity":
                    if connector_cavity_counter == 0:
                        from_connector_cavity = instance3.get("instance_name")
                        from_connector = instances_list.attribute_of(from_connector_cavity, "parent_instance")
                    elif connector_cavity_counter == 1:
                        to_connector_cavity = instance3.get("instance_name")
                        to_connector = instances_list.attribute_of(to_connector_cavity, "parent_instance")
                    else:
                        raise ValueError(f"There are 3 or more cavities specified in circuit {circuit_name} but expected two (to, from) when building wirelist.")
                    connector_cavity_counter += 1

        # look for cavities that have parents that match a to or from connector
        for instance4 in instances_list.read_instance_rows():
            if instance4.get("circuit_id") == circuit_name:
                if instance4.get("item_type") == "Contact":
                    if instance4.get("parent_instance") == from_connector:
                        from_special_contact = instance4.get("instance_name")
                    elif instance4.get("parent_instance") == to_connector:
                        to_special_contact = instance4.get("instance_name")

        # find conductor and cable
        for instance5 in instances_list.read_instance_rows():
            if instance5.get("circuit_id") == circuit_name:
                if instance5.get("item_type") == "Conductor":
                    conductor_identifier = instance5.get("print_name")
                    cable = instance5.get("parent_instance")
                    length = instance5.get("length")
                    
        wirelist.add({
            "Circuit_name": circuit_name,
            "Length": length,
            "Cable": cable,
            "Conductor_identifier": conductor_identifier,
            "From_connector": instances_list.attribute_of(from_connector, "print_name"),
            "From_connector_cavity": instances_list.attribute_of(from_connector_cavity, "print_name"),
            "From_special_contact": from_special_contact,
            "To_special_contact": to_special_contact,
            "To_connector": instances_list.attribute_of(to_connector, "print_name"),
            "To_connector_cavity": instances_list.attribute_of(to_connector_cavity, "print_name"),
        })

#=============== MAKE A PRETTY WIRELIST #===============
wirelist.tsv_to_xls()