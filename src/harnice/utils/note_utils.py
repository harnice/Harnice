from harnice import fileio
from harnice.lists import instances_list, rev_history

note_counter = 1


def new_note(
    note_type,  # rev_change_callout, bom_item, part_name, build_note, etc
    note_text,  # content of the note, must be unique
    bubble_text=None,  # text you want to appear in the bubble
    note_number=None,  # if it's numbered (bom, rev, etc)
    shape_mpn=None,
    shape_lib_subpath=None,
    shape_lib_repo="https://github.com/harnice/harnice-library-public",
    affectedinstances=[],
):

    if not shape_mpn:
        shape_mpn = note_type

    global note_counter

    instances_list.new_instance(
        f"note-{note_counter}",
        {
            "item_type": "note",
            "note_type": note_type,
            "print_name": note_text,  # interchangeable with note_text
            "note_text": note_text,
            "mpn": shape_mpn,
            "lib_repo": shape_lib_repo,
            "lib_subpath": shape_lib_subpath,
            "note_number": note_number,
        },
    )

    if not affectedinstances == []:
        for affected_instance in affectedinstances:
            instances_list.new_instance(
                f"note-{note_counter}-{affected_instance}",
                {
                    "item_type": "flagnote",
                    "print_name": bubble_text,
                    "parent_instance": affected_instance,
                    "note_type": note_type,
                    "note_text": note_text,
                    "mpn": shape_mpn,
                    "lib_repo": shape_lib_repo,
                    "lib_subpath": shape_lib_subpath,
                    "note_parent": f"note-{note_counter}",
                    "note_number": note_number,
                },
            )

    note_counter += 1


def assign_buildnote_numbers():
    build_note_counter = 0
    for instance in fileio.read_tsv("instances list"):
        if instance.get("note_type") == "build_note":
            if instance.get("item_type") == "note":
                build_note_counter += 1
            instances_list.modify(
                instance.get("instance_name"),
                {"note_number": build_note_counter, "print_name": build_note_counter},
            )


def make_rev_history_notes():
    rev_rows = fileio.read_tsv("revision history")
    for rev in rev_rows:
        affected_instances = rev_history.info(
            rev=rev.get("rev"), field="affectedinstances"
        )
        if not affected_instances == []:
            new_note(
                note_type="rev_change_callout",
                note_text=rev.get("revisionupdates"),
                note_number=rev.get("rev"),
                bubble_text=rev.get("rev"),
                shape_mpn="rev_change_callout",
                shape_lib_repo="https://github.com/harnice/harnice-library-public",
                affectedinstances=affected_instances,
            )


def combine_notes(instance_names):
    # instance_names is a list of note instances
    raise NotImplementedError("to do")
