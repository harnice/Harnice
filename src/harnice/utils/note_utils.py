from sre_parse import NOT_LITERAL_IGNORE
from harnice import fileio
from harnice.lists import instances_list, rev_history

note_counter = 1

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
    note_number=None,
    shape = None,
    shape_lib_subpath = None,
    shape_lib_repo = None,
    affectedinstances = []):

    global note_counter

    instances_list.new_instance(f"note-{note_counter}", {
        "item_type": "note",
        "note_type": note_type,
        "print_name": note_text, #interchangeable with note_text
        "note_text": note_text,
        "shape": shape,
        "shape_lib_repo": shape_lib_repo,
        "shape_lib_subpath": shape_lib_subpath,
        "note_number": note_number
    })

    if not affectedinstances == []:
        for affected_instance in affectedinstances:
            instances_list.new_instance(f"note-{note_counter}-{affected_instance}",{
                "item_type": "note-affected",
                "parent_instance": affected_instance,
                "note_type": note_type,
                "print_name": note_text, #interchangeable with note_text
                "note_text": note_text,
                "shape": shape,
                "shape_lib_repo": shape_lib_repo,
                "shape_lib_subpath": shape_lib_subpath,
                "note_parent": f"note-{note_counter}",
                "note_number": note_number
            })

    note_counter += 1


def assign_buildnote_numbers():
    build_note_counter = 0
    for instance in fileio.read_tsv("instances list"):
        if instance.get("note_type") == "build_note":
            if instance.get("item_type") == "note":
                build_note_counter += 1
            instances_list.modify(instance.get("instance_name"), {
                "note_number": build_note_counter
            })

def make_rev_history_notes():
    rev_rows = fileio.read_tsv("revision history")
    for rev in rev_rows:
        affected_instances = rev_history.info(rev=rev.get("rev"),field="affectedinstances")
        if not affected_instances == []:
            new_note(
                note_type="rev_history_callout",
                note_text=rev.get("revisionupdates"),
                note_number=rev.get("rev"),
                shape="rev_history_callout",
                shape_lib_repo="https://github.com/harnice/harnice-library-public",
                affectedinstances=affected_instances
            )

def combine_notes(instance_names):
    #instance_names is a list of note instances
    raise NotImplementedError("to do")