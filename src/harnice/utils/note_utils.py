import ast
from harnice import fileio
from harnice.lists import instances_list, rev_history
from harnice import state

note_counter = 1


def new_note(
    note_type,
    note_text,
    note_number=None,
    bubble_text=None,
    shape_mpn=None,
    shape_lib_subpath=None,
    shape_lib_repo="https://github.com/harnice/harnice-library-public",
    affectedinstances=None,
):
    """
    Creates or updates a note instance.

    Behavior:
    - If a note with identical (note_type, note_text) already exists:
        * If either existing or new affectedinstances is empty → ERROR.
        * Else → merge affectedinstances into existing note, DO NOT create a new one.
    """

    if not shape_mpn:
        shape_mpn = note_type

    global note_counter

    # ------------------------------------------------------------
    # 1. Search for an existing identical note
    # ------------------------------------------------------------
    existing = None
    for instance in fileio.read_tsv("instances list"):
        if (
            instance.get("item_type") == "note"
            and instance.get("note_type") == note_type
            and instance.get("note_text") == note_text
        ):
            existing = instance
            break

    # Normalize new affectedinstances
    new_affected_instances = affectedinstances or []
    if isinstance(new_affected_instances, str):
        import ast
        try:
            new_affected_instances = ast.literal_eval(new_affected_instances)
        except Exception:
            raise ValueError(f"Malformed affectedinstances value: {affectedinstances}")

    # ------------------------------------------------------------
    # 2. CASE A — Existing note found
    # ------------------------------------------------------------
    if existing:
        # Parse existing list safely
        old_affected_instances_raw = existing.get("note_affected_instances")
        if isinstance(old_affected_instances_raw, str):
            import ast
            try:
                old_affected_instances = ast.literal_eval(old_affected_instances_raw)
            except Exception:
                old_affected_instances = []
        else:
            old_affected_instances = old_affected_instances_raw or []

        # A.1 — If either side lacks affected instances → ERROR
        if not old_affected_instances or not new_affected_instances:
            raise ValueError(
                f"Note '{note_type}:{note_text}' already exists but "
                "one of the notes has no affected_instances. "
                "This note has already been assigned."
            )

        # A.2 — Merge and deduplicate into existing instance
        merged = list(dict.fromkeys(old_affected_instances + new_affected_instances))  # keep order, remove dupes
        existing["note_affected_instances"] = merged

        # Write modification back to instances_list
        instances_list.modify(existing.get("instance_name"), {"note_affected_instances": merged})
        return existing

    # ------------------------------------------------------------
    # 3. CASE B — No existing note, create a new one
    # ------------------------------------------------------------
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
            "note_affected_instances": new_affected_instances,
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
    affected_instances = rev_history.info(rev=rev.get("rev"), field="affectedinstances")

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
        "instance_name": f"note-build_note-{note_instance.get('instance_name')}-{affected_instance.get('instance_name')}",
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


def get_lib_build_notes(instance):
    """
    Returns list of build_notes for this instance from the TSV row.
    Safely parses with ast.literal_eval.
    Always returns a Python list.
    """

    raw = instance.get("lib_build_notes")

    if not raw or raw in ["", None]:
        return []

    try:
        # Expecting a string representation of a list
        parsed = ast.literal_eval(raw)

        # Ensure it's actually a list
        return parsed if isinstance(parsed, list) else []

    except Exception:
        # Malformed literal → fail safe
        return []

def get_lib_tools(instance):
    """
    Returns list of tools for this instance from the TSV row.
    Safely parses with ast.literal_eval.
    Always returns a Python list.
    """

    raw = instance.get("lib_tools")

    if not raw or raw in ["", None]:
        return []

    try:
        # Expecting a string representation of a list
        parsed = ast.literal_eval(raw)

        # Ensure it's actually a list
        return parsed if isinstance(parsed, list) else []

    except Exception:
        # Malformed literal → fail safe
        return []


def combine_notes(keep_note_text, merge_note_texts, note_type=None):
    keep_note_instance = None
    merge_note_instances_raw = []
    for instance in fileio.read_tsv("instances list"):
        if instance.get("note_text") in [None, ""]:
            continue
        if instance.get("note_text") == keep_note_text:
            if note_type:
                if instance.get("note_type") in note_type:
                    keep_note_instance = instance
            else:
                keep_note_instance = instance
        if instance.get("note_text") in merge_note_texts:
            if note_type:
                if instance.get("note_type") in note_type:
                    merge_note_instances_raw.append(instance)
            else:
                merge_note_instances_raw.append(instance)

    merge_note_instances_parsed = []
    for instance in merge_note_instances_raw:
        merge_note_instances_parsed.append(parse_note_instance(instance))

    new_affected_instances = set()

    for merged_note_instance in merge_note_instances_parsed:
        for affected_instance in merged_note_instance.get("note_affected_instances"):
            new_affected_instances.add(affected_instance)
        instances_list.remove_instance(merged_note_instance)

    for affected_instance in parse_note_instance(keep_note_instance).get("note_affected_instances"):
        new_affected_instances.add(affected_instance)

    instances_list.modify(keep_note_instance.get("instance_name"), {
        "note_affected_instances": list(new_affected_instances)}
    )
