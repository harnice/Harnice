from harnice import fileio
from harnice.lists import instances_list


def compile_build_notes():
    # add build_note itemtypes to list (separate from the flagnote itemtype) to form source of truth for the list itself
    for instance in fileio.read_tsv("instances list"):
        if (
            instance.get("item_type") == "flagnote"
            and instance.get("note_type") == "build_note"
        ):
            instances_list.modify(
                instance.get("instance_name"),
                {"note_number": instance.get("bubble_text")},
            )

    for instance in fileio.read_tsv("instances list"):
        if (
            instance.get("item_type") == "flagnote"
            and instance.get("note_type") == "build_note"
        ):
            build_note_text = instance.get("note_text")
            note_number = instance.get("note_number")

            # does this build_note exist as an instance yet?
            already_exists = False
            for instance2 in fileio.read_tsv("instances list"):
                if (
                    instance2.get("item_type") == "build_note"
                    and instance2.get("note_text") == build_note_text
                ):
                    already_exists = True

            # if not, make it
            if not already_exists:
                instances_list.new_instance(
                    f"build_note-{instance.get('bubble_text')}",
                    {
                        "item_type": "build_note",
                        "note_text": build_note_text,
                        "note_number": note_number,
                    },
                )
                if instance.get("lib_repo") not in [None, ""]:
                    if instance.get("parent_instance") not in [None, ""]:
                        instances_list.modify(
                            f"build_note-{instance.get('bubble_text')}",
                            {
                                "mpn": instance.get("mpn"),
                                "lib_repo": instance.get("lib_repo"),
                            },
                        )


def assign_output_csys():
    for current_affected_instance_candidate in fileio.read_tsv("instances list"):
        processed_affected_instances = []
        current_affected_instance = None
        if current_affected_instance_candidate.get("item_type") == "flagnote":
            if (
                current_affected_instance_candidate.get("parent_instance")
                not in processed_affected_instances
            ):
                current_affected_instance = current_affected_instance_candidate.get(
                    "parent_instance"
                )

        # now that you have a not-yet traversed affected instance
        flagnote_counter = 1
        for instance in fileio.read_tsv("instances list"):
            if instance.get("item_type") == "flagnote":
                if instance.get("parent_instance") == current_affected_instance:
                    instances_list.modify(
                        instance.get("instance_name"),
                        {
                            "parent_csys_instance_name": current_affected_instance,
                            "parent_csys_outputcsys_name": f"flagnote-{flagnote_counter}",
                            "absolute_rotation": 0,
                        },
                    )
                    instances_list.new_instance(
                        f"{instance.get('instance_name')}.leader",
                        {
                            "parent_csys_instance_name": current_affected_instance,
                            "parent_instance": instance.get("instance_name"),
                            "item_type": "flagnote-leader",
                            "location_type": "node",
                            "parent_csys_outputcsys_name": f"flagnote-leader-{flagnote_counter}",
                            "absolute_rotation": 0,
                            "connector_group": instances_list.attribute_of(
                                instance.get("instance_name"), "connector_group"
                            ),
                        },
                        ignore_duplicates=True,
                    )
                    flagnote_counter += 1
