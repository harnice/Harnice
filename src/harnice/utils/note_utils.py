from harnice import fileio
from harnice.lists import instances_list

note_counter = 1
build_note_counter = 1

def assign_output_csys(flagnote_number, affected_instance):
    for current_affected_instance_candidate in fileio.read_tsv("instances list"):
        processed_affected_instances = []
        current_affected_instance = None
        if current_affected_instance_candidate.get("item_type") == "flag_note":
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
            if instance.get("item_type") == "flag_note":
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


def new_note(
    note_type, # rev_change_callout, bom_item, part_name, build_note, etc
    note_text, # content of the note, must be unique
    shape = None,
    shape_lib_subpath = None,
    shape_lib_repo = None,
    affectedinstances = None):

    global note_counter

    for instance in fileio.read_tsv("instances list"):
        if instance.get("note_text") == note_text:
            updated_affectedinstances = []

            if instance.get("affectedinstances"):
                updated_affectedinstances = instance.get("affectedinstances").strip().split(";")

            updated_affectedinstances.append(affectedinstances)

            instances_list.modify(instance.get("instance_name"), {
                "affectedinstances": updated_affectedinstances
            })

    instances_list.new_instance(f"note-{note_counter}", {
        "item_type": "note",
        "note_type": note_type,
        "print_name": note_text,
        "note_text": note_text,
        "shape": shape,
        "shape_lib_repo": shape_lib_repo,
        "shape_lib_subpath": shape_lib_subpath,
        "affectedinstances": affectedinstances
    })

    note_counter += 1