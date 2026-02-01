??? note "Default harness feature tree"
    ```python
    
    import os
    from harnice import fileio, state
    from harnice.utils import (
        circuit_utils,
        formboard_utils,
        note_utils,
        library_utils,
        feature_tree_utils,
    )
    from harnice.lists import (
        instances_list,
        post_harness_instances_list,
        rev_history,
    )
    
    
    # ===========================================================================
    #                   build_macro SCRIPTING
    # ===========================================================================
    system_pn = "system_part_number" # enter your system part number
    system_rev = "system_revision" # enter your system revision
    system_base_directory = fileio.get_path_to_project(system_pn) # add the path to project_locations.csv in the root of harnice
    system_target_net = "target_net" # enter the net you're building from
    
    feature_tree_utils.run_macro(
        "import_harness_from_harnice_system",
        "harness_builder",
        "https://github.com/harnice/harnice",
        "harness-from-system-1",
        system_pn=f"{system_pn}",
        system_rev=f"{system_rev}",
        path_to_system_rev=os.path.join(
            system_base_directory,
            f"{system_pn}-{system_rev}",
        ),
        target_net=system_target_net,
        manifest_nets=[system_target_net],
    )
    
    rev_history.overwrite(
        {
            "desc": f"HARNESS '{system_target_net}' FROM SYSTEM '{system_pn}-{system_rev}'",
        }
    )
    
    
    # ===========================================================================
    #                  HARNESS BUILD RULES
    # ===========================================================================
    # example: assign a special contact to one specific conductor
    instances = fileio.read_tsv("instances list")
    circuit_instance = None
    connector_at_end_a = None
    for instance in instances:
        if instance.get("channel_group") == "channel-MIC2.out1-PREAMP1.in2":
            if instance.get("signal_of_channel_type") == "pos":
                if instance.get("item_type") == "circuit":
                    circuit_instance = instance
                    connector_at_end_a = instances_list.attribute_of(instance.get("node_at_end_a"), "connector_group")
    new_instance_name = f"{circuit_instance.get("instance_name")}-special_contact"
    circuit_id = int(circuit_instance.get("circuit_id"))
    instances_list.new_instance(
        new_instance_name, {
            "bom_line_number": True,
            "mpn": "TXPS20",
            "item_type": "contact",
            "location_type": "node",
            "circuit_id": circuit_id,
            "connector_group": connector_at_end_a
        }
    )
    circuit_utils.squeeze_instance_between_ports_in_circuit(
        new_instance_name, circuit_id, 1
    )
    
    # example: add a backshell
    for instance in instances:
        if instance.get("instance_name") in ["X1.B.conn", "PREAMP2.in2.conn"]:
            instances_list.new_instance(f"{instance.get("connector_group")}.bs", {
                "bom_line_number": True,
                "mpn": "M85049-90_9Z03",
                "item_type": "backshell",
                "parent_instance": instance.get("instance_name"),
                "location_type": "node",
                "connector_group": instance.get("connector_group"),
                "parent_csys_instance_name": (instances_list.instance_in_connector_group_with_item_type(instance.get("connector_group"), "node")).get("instance_name"),
                "parent_csys_outputcsys_name": "origin",
                "lib_repo": "https://github.com/harnice/harnice"
            })
            instances_list.modify(instance.get("instance_name"), {
                "parent_csys_instance_name": f"{instance.get("connector_group")}.bs",
                "parent_csys_outputcsys_name": "connector",
            })
    
    
    # ===========================================================================
    #                   IMPORT PARTS FROM LIBRARY FOR GENERAL USE
    # ===========================================================================
    for instance in fileio.read_tsv("instances list"):
        if instance.get("item_type") in ["connector", "backshell"]:
            if instance.get("instance_name") not in ["X100"]:
                if instance.get("mpn") not in ["TXPA20"]:
                    library_utils.pull(instance)
    
    # ===========================================================================
    #                  PROCESS HARNESS LAYOUT GRAPH
    # ===========================================================================
    formboard_utils.validate_nodes()
    
    instances = fileio.read_tsv("instances list")
    for instance in instances:
        if instance.get("item_type") == "cable":
            for instance2 in instances:
                if instance2.get("parent_instance") == instance.get("instance_name"):
                    if instance2.get("item_type") == "conductor":
                        instances_list.modify(
                            instance.get("instance_name"),
                            {
                                "node_at_end_a": instances_list.instance_in_connector_group_with_item_type(
                                    instances_list.attribute_of(
                                        instance2.get("node_at_end_a"), "connector_group"
                                    ),
                                    "node",
                                ).get("instance_name"),
                                "node_at_end_b": instances_list.instance_in_connector_group_with_item_type(
                                    instances_list.attribute_of(
                                        instance2.get("node_at_end_b"), "connector_group"
                                    ),
                                    "node",
                                ).get("instance_name"),
                            },
                        )
                        break
    
    for instance in fileio.read_tsv("instances list"):
        if instance.get("item_type") in ["conductor", "cable", "net-channel"]:
            formboard_utils.map_instance_to_segments(instance)
    
    for instance in fileio.read_tsv("instances list"):
        if instance.get("item_type") in ["conductor", "cable"]:
            length = 0
            for instance2 in fileio.read_tsv("instances list"):
                if instance2.get("parent_instance") == instance.get("instance_name"):
                    if instance2.get("length", "").strip():
                        length += int(instance2.get("length").strip())
            instances_list.modify(instance.get("instance_name"), {"length": length})
    
    # ===========================================================================
    #                   ASSIGN BOM LINE NUMBERS
    # ===========================================================================
    for instance in fileio.read_tsv("instances list"):
        if instance.get("item_type") in ["connector", "cable", "backshell"]:
            instances_list.modify(instance.get("instance_name"), {"bom_line_number": True})
    instances_list.assign_bom_line_numbers()
    
    # ===========================================================================
    #       ASSIGN PRINT NAMES
    # ===========================================================================
    for x in range(2):
        for instance in fileio.read_tsv("instances list"):
            if instance.get("item_type") == "connector_cavity":
                instance_name = instance.get("instance_name", "")
                print_name = f"cavity {instance_name.split(".")[-1] if "." in instance_name else instance_name}"
                instances_list.modify(instance_name, {"print_name": print_name})
    
            elif instance.get("item_type") in ["conductor", "conductor-segment"]:
                instances_list.modify(instance.get("instance_name"), {
                    "print_name": f"'{instance.get("cable_identifier")}' of '{instances_list.attribute_of(instance.get("cable_group"), "print_name")}'"
                })
    
            elif instance.get("item_type") == "net-channel":
                print_name = f"'{instance.get("this_channel_from_device_channel_id")}' of '{instance.get("this_channel_from_device_refdes")}' to '{instance.get("this_channel_to_device_channel_id")}' of '{instance.get("this_channel_to_device_refdes")}'"
                instances_list.modify(instance.get("instance_name"), {"print_name": print_name})
    
            elif instance.get("item_type") == "net-channel-segment":
                print_name = f"'{instances_list.attribute_of(instance.get("parent_instance"), "this_channel_from_device_channel_id")}' of '{instances_list.attribute_of(instance.get("parent_instance"), "this_channel_from_device_refdes")}' to '{instances_list.attribute_of(instance.get("parent_instance"), "this_channel_to_device_channel_id")}' of '{instances_list.attribute_of(instance.get("parent_instance"), "this_channel_to_device_refdes")}'"
                instances_list.modify(instance.get("instance_name"), {"print_name": print_name})
    
            elif instance.get("item_type") == "connector":
                print_name = f"{instance.get("connector_group")}"
                instances_list.modify(instance.get("instance_name"), {"print_name": print_name})
    
            elif instance.get("item_type") == "cable-segment":
                print_name = f"{instance.get("cable_group")}"
                instances_list.modify(instance.get("instance_name"), {"print_name": print_name})
    
            elif instance.get("item_type") == "contact":
                print_name = instance.get("mpn")
                instances_list.modify(
                    instance.get("instance_name"),
                    {"print_name": print_name}
                )
    
            else:
                instances_list.modify(instance.get("instance_name"), {"print_name": instance.get("instance_name")})
    
    # ===========================================================================
    #                  ADD BUILD NOTES
    # ===========================================================================
    for rev_row in fileio.read_tsv("revision history"):
        if rev_row.get("rev") == state.rev:
            note_utils.make_rev_history_notes(rev_row)
    
    for instance in fileio.read_tsv("instances list"):
        for note in note_utils.get_lib_build_notes(instance):
            note_utils.new_note(
                "build_note",
                note,
                affectedinstances=[instance.get("instance_name")]
            )
    
    note_utils.assign_buildnote_numbers()
    
    # example: add notes to describe actions
    # note_utils.new_note(
    #     "build_note",
    #     "do this",
    #     affectedinstances=["X1.B.conn"]
    # )
    # note_utils.new_note(
    #     "build_note",
    #     "do that"
    # )
    
    # example: combine buildnotes if their texts are similar
    #note_utils.combine_notes("Torque backshell to connector at 40 in-lbs","Torque backshell to connector at about 40 in-lbs")
    
    
    # ===========================================================================
    #                  PUT TOGETHER FORMBOARD SVG INSTANCE CONTENT
    # ===========================================================================
    instances = fileio.read_tsv("instances list")
    note_instances = []
    for instance in instances:
        if instance.get("item_type") == "note":
            note_instances.append(note_utils.parse_note_instance(instance))
    
    formboard_overview_instances = []
    formboard_detail_instances = []
    for instance in instances:
        if instance.get("item_type") not in ["connector", "backshell", "segment", "node", "origin"]:
            continue
    
        formboard_overview_instances.append(instance)
        formboard_detail_instances.append(instance)
    
        detail_flag_note_counter = 1
        overview_flag_note_counter = 1
    
        if instance.get("item_type") in ["connector", "backshell"]:
            formboard_detail_instances.append(note_utils.make_bom_flagnote(instance, f"flagnote-{detail_flag_note_counter}"))
            detail_flag_note_counter += 1
    
            formboard_detail_instances.append(note_utils.make_part_name_flagnote(instance, f"flagnote-{detail_flag_note_counter}"))
            detail_flag_note_counter += 1
    
        if instance.get("item_type") == "connector":
            formboard_overview_instances.append(note_utils.make_part_name_flagnote(instance, f"flagnote-{overview_flag_note_counter}"))
            overview_flag_note_counter += 1
    
        for note_instance in note_instances:
            if note_instance.get("note_type") == "build_note":
                if instance.get("instance_name") in note_instance.get("note_affected_instances"):
                    formboard_detail_instances.append(
                        note_utils.make_buildnote_flagnote(note_instance, instance, f"flagnote-{detail_flag_note_counter}")
                    )
                    detail_flag_note_counter += 1
    
            if note_instance.get("note_type") == "rev_change_callout":
                if instance.get("instance_name") in note_instance.get("note_affected_instances"):
                    formboard_detail_instances.append(
                        note_utils.make_rev_change_flagnote(note_instance, instance, f"flagnote-{detail_flag_note_counter}")
                    )
                    detail_flag_note_counter += 1
    
    # ===========================================================================
    #                  BUILD HARNESS OUTPUTS
    # ===========================================================================
    instances = fileio.read_tsv("instances list")
    scales = {"A": 0.25, "B": 0.3, "C": 1}
    
    feature_tree_utils.run_macro(
        "bom_exporter_bottom_up",
        "harness_artifacts",
        "https://github.com/harnice/harnice",
        artifact_id="bom-1",
    )
    feature_tree_utils.run_macro(
        "standard_harnice_formboard",
        "harness_artifacts",
        "https://github.com/harnice/harnice",
        artifact_id="formboard-overview",
        scale=scales.get("A"),
        input_instances=formboard_overview_instances,
    )
    feature_tree_utils.run_macro(
        "standard_harnice_formboard",
        "harness_artifacts",
        "https://github.com/harnice/harnice",
        artifact_id="formboard-detail",
        scale=scales.get("C"),
        input_instances=formboard_detail_instances,
    )
    feature_tree_utils.run_macro(
        "segment_visualizer",
        "harness_artifacts",
        "https://github.com/harnice/harnice",
        artifact_id="cable_layout-1",
        scale=scales.get("A"),
        item_type="cable-segment",
        segment_spacing_inches=0.1,
    )
    feature_tree_utils.run_macro(
        "segment_visualizer",
        "harness_artifacts",
        "https://github.com/harnice/harnice",
        artifact_id="conductor-layout-1",
        scale=scales.get("A"),
        item_type="conductor-segment",
        segment_spacing_inches=0.1,
    )
    feature_tree_utils.run_macro(
        "segment_visualizer",
        "harness_artifacts",
        "https://github.com/harnice/harnice",
        artifact_id="channel-layout-1",
        scale=scales.get("B"),
        item_type="net-channel-segment",
        segment_spacing_inches=0.1,
    )
    feature_tree_utils.run_macro(
        "circuit_visualizer",
        "harness_artifacts",
        "https://github.com/harnice/harnice",
        artifact_id="circuitviz-1",
        input_circuits=instances,
    )
    feature_tree_utils.run_macro(
        "revision_history_table",
        "harness_artifacts",
        "https://github.com/harnice/harnice",
        artifact_id="revhistory-1",
    )
    
    build_notes_list_instances = []
    for instance in fileio.read_tsv("instances list"):
        if instance.get("item_type") == "note" and instance.get("note_type") == "build_note":
            build_notes_list_instances.append(instance)
    
    feature_tree_utils.run_macro(
        "build_notes_table",
        "harness_artifacts",
        "https://github.com/harnice/harnice",
        artifact_id="build_notes_table-1",
        input_instances=build_notes_list_instances,
    )
    feature_tree_utils.run_macro(
        "pdf_generator",
        "harness_artifacts",
        "https://github.com/harnice/harnice",
        artifact_id="pdf_drawing-1",
        scales=scales,
    )
    
    
    # ensure the system that this harness was built from contains the complete updated instances list
    post_harness_instances_list.push(
        system_base_directory,
        (system_pn, system_rev),
    )
    
    
    # for convenience, move any pdf to the base directory of the harness
    feature_tree_utils.copy_pdfs_to_cwd()
    ```