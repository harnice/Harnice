import ast
from harnice import fileio
from harnice.lists import instances_list, rev_history
from harnice import state

note_counter = 1

def new_note(
    note_type,  # rev_change_callout, bom_item, part_name, build_note, etc
    note_text,  # content of the note, must be unique
    note_number=None,  # if it's numbered (bom, rev, etc)
    bubble_text=None,
    shape_mpn=None,
    shape_lib_subpath=None,
    shape_lib_repo="https://github.com/harnice/harnice-library-public",
    affectedinstances=None,
):

    if not shape_mpn:
        shape_mpn = note_type

    global note_counter

    instances_list.new_instance(
        f"note-{note_counter}",
        {
            "item_type": "note",
            "note_type": note_type,
            "print_name": bubble_text,
            "note_text": note_text,
            "mpn": shape_mpn,
            "lib_repo": shape_lib_repo,
            "lib_subpath": shape_lib_subpath,
            "note_number": note_number,
            "note_affected_instances": affectedinstances,
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


def make_rev_history_notes(rev):
    affected_instances = rev_history.info(
        rev=rev.get("rev"),
        field="affectedinstances"
    )

    if affected_instances:  # safer + more pythonic
        new_note(
            note_type="rev_change_callout",
            note_text=rev.get("revisionupdates"),
            note_number=rev.get("rev"),
            bubble_text=rev.get("rev"),
            shape_mpn="rev_change_callout",
            shape_lib_repo="https://github.com/harnice/harnice-library-public",
            affectedinstances=affected_instances,
        )


def make_bom_flagnote(affected_instance, output_csys_name):
    return {
        "net": state.net,
        "instance_name": f"note-bom_item-{affected_instance.get('instance_name')}",
        "print_name": affected_instance.get("bom_line_number"),
        "mpn": "bom_item",
        "item_type": "flagnote",
        "parent_instance": affected_instance.get("instance_name"),
        "segment_group": affected_instance.get("segment_group"),
        "connector_group": affected_instance.get("connector_group"),
        "parent_csys_instance_name": affected_instance.get("instance_name"),
        "parent_csys_outputcsys_name": output_csys_name,
        "absolute_rotation": 0,
        "note_type": "bom_item",
        "note_affected_instances": [affected_instance.get("instance_name")],
        "lib_repo": "https://github.com/harnice/harnice-library-public",
    }

def make_part_name_flagnote(affected_instance, output_csys_name):
    return {
        "net": state.net,
        "instance_name": f"note-part_name-{affected_instance.get('instance_name')}",
        "print_name": affected_instance.get("print_name"),
        "mpn": "part_name",
        "item_type": "flagnote",
        "parent_instance": affected_instance.get("instance_name"),
        "segment_group": affected_instance.get("segment_group"),
        "connector_group": affected_instance.get("connector_group"),
        "parent_csys_instance_name": affected_instance.get("instance_name"),
        "parent_csys_outputcsys_name": output_csys_name,
        "absolute_rotation": 0,
        "note_type": "part_name",
        "note_affected_instances": [affected_instance.get("instance_name")],
        "lib_repo": "https://github.com/harnice/harnice-library-public",
    }

def make_buildnote_flagnote(note_instance, affected_instance, output_csys_name):
    return {
        "net": state.net,
        "instance_name": f"note-build_note-{note_instance.get('instance_name')}",
        "print_name": note_instance.get("print_name"),
        "mpn": "build_note",
        "item_type": "flagnote",
        "parent_instance": affected_instance.get("instance_name"),
        "segment_group": affected_instance.get("segment_group"),
        "connector_group": affected_instance.get("connector_group"),
        "parent_csys_instance_name": affected_instance.get("instance_name"),
        "parent_csys_outputcsys_name": output_csys_name,
        "absolute_rotation": 0,
        "note_type": "build_note",
        "note_affected_instances": [affected_instance.get("instance_name")],
        "lib_repo": "https://github.com/harnice/harnice-library-public",
    }

def make_rev_change_flagnote(note_instance, affected_instance, output_csys_name):
    return {
        "net": state.net,
        "instance_name": f"note-rev_change_callout-{note_instance.get('instance_name')}-{affected_instance.get('instance_name')}",
        "print_name": note_instance.get("print_name"),
        "mpn": "rev_change_callout",
        "item_type": "flagnote",
        "parent_instance": affected_instance.get("instance_name"),
        "segment_group": affected_instance.get("segment_group"),
        "connector_group": affected_instance.get("connector_group"),
        "parent_csys_instance_name": affected_instance.get("instance_name"),
        "parent_csys_outputcsys_name": output_csys_name,
        "absolute_rotation": 0,
        "note_type": "rev_change_callout",
        "note_affected_instances": [affected_instance.get("instance_name")],
        "lib_repo": "https://github.com/harnice/harnice-library-public",
    }

def parse_note_instance(instance):
    """
    Return a full copy of `instance`, but with note_affected_instances
    parsed into a real Python list (or left alone if blank).
    """
    parsed = {}

    for key, value in instance.items():
        if key == "note_affected_instances":
            if isinstance(value, str) and value.strip():
                try:
                    parsed[key] = ast.literal_eval(value)
                except Exception:
                    parsed[key] = []  # fallback if malformed
            else:
                parsed[key] = []
        else:
            parsed[key] = value

    return parsed


def combine_notes(instance_names):
    # instance_names is a list of note instances
    raise NotImplementedError("to do")
