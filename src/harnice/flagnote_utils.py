import os
import csv
import re
from harnice import fileio, instances_list, component_library

# === Global Columns Definition ===
MANUAL_FLAGNOTES_COLUMNS = [
    "note_type",
    "note_text",
    "shape",
    "shape_lib_repo",
    "bubble_text",
    "affectedinstances",
]


def ensure_manual_list_exists():
    if not os.path.exists(fileio.path("flagnotes manual")):
        with open(
            fileio.path("flagnotes manual"), "w", newline="", encoding="utf-8"
        ) as f:
            writer = csv.DictWriter(
                f, fieldnames=MANUAL_FLAGNOTES_COLUMNS, delimiter="\t"
            )
            writer.writeheader()


def read_manual_list():
    with open(
        fileio.path("flagnotes manual"), newline="", encoding="utf-8"
    ) as f_manual:
        return list(csv.DictReader(f_manual, delimiter="\t"))


def read_revhistory():
    with open(fileio.path("revision history"), newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            yield row


def make_note_drawings(formboard_dir):
    instances = instances_list.read_instance_rows()

    for instance in instances:
        if instance.get("item_type", "").lower() != "flagnote":
            continue

        instance_name = instance.get("instance_name")
        parent_instance = instance.get("parent_instance", "").strip()

        destination_directory = os.path.join(
            formboard_dir, instance.get("instance_name")
        )
        os.makedirs(destination_directory, exist_ok=True)

        # === Pull library item ===
        component_library.pull_item_from_library(
            lib_repo=instance.get("lib_repo"),
            product="flagnotes",
            mpn=instance.get("mpn"),
            destination_directory=destination_directory,
            used_rev=None,
            item_name=instance_name,
        )

        # === Replace placeholder in SVG ===
        drawing_path = os.path.join(
            destination_directory, f"{instance_name}-drawing.svg"
        )
        if not os.path.exists(drawing_path):
            print(f"[WARN] Drawing not found: {drawing_path}")
            continue

        with open(drawing_path, "r", encoding="utf-8") as f:
            svg = f.read()

        svg = re.sub(r">flagnote-text<", f">{instance.get('bubble_text')}<", svg)

        with open(drawing_path, "w", encoding="utf-8") as f:
            f.write(svg)


def compile_buildnotes():
    # add buildnote itemtypes to list (separate from the flagnote itemtype) to form source of truth for the list itself
    for instance in instances_list.read_instance_rows():
        if (
            instance.get("item_type") == "Flagnote"
            and instance.get("note_type") == "buildnote"
        ):
            instances_list.modify(
                instance.get("instance_name"),
                {"note_number": instance.get("bubble_text")},
            )

    for instance in instances_list.read_instance_rows():
        if (
            instance.get("item_type") == "Flagnote"
            and instance.get("note_type") == "buildnote"
        ):
            buildnote_text = instance.get("note_text")
            note_number = instance.get("note_number")

            # does this buildnote exist as an instance yet?
            already_exists = False
            for instance2 in instances_list.read_instance_rows():
                if (
                    instance2.get("item_type") == "Buildnote"
                    and instance2.get("note_text") == buildnote_text
                ):
                    already_exists = True

            # if not, make it
            if already_exists == False:
                instances_list.add_unless_exists(
                    f"buildnote-{instance.get('bubble_text')}",
                    {
                        "item_type": "Buildnote",
                        "note_text": buildnote_text,
                        "note_number": note_number,
                    },
                )
                if instance.get("lib_repo") not in [None, ""]:
                    if instance.get("parent_instance") not in [None, ""]:
                        instances_list.modify(
                            f"buildnote-{instance.get('bubble_text')}",
                            {
                                "mpn": instance.get("mpn"),
                                "lib_repo": instance.get("lib_repo"),
                            },
                        )


def assign_output_csys():
    for current_affected_instance_candidate in instances_list.read_instance_rows():
        processed_affected_instances = []
        current_affected_instance = None
        if current_affected_instance_candidate.get("item_type") == "Flagnote":
            if (
                current_affected_instance_candidate.get("parent_instance")
                not in processed_affected_instances
            ):
                current_affected_instance = current_affected_instance_candidate.get(
                    "parent_instance"
                )

        # now that you have a not-yet traversed affected instance
        flagnote_counter = 1
        for instance in instances_list.read_instance_rows():
            if instance.get("item_type") == "Flagnote":
                if instance.get("parent_instance") == current_affected_instance:
                    instances_list.modify(
                        instance.get("instance_name"),
                        {
                            "parent_csys_instance_name": current_affected_instance,
                            "parent_csys_outputcsys_name": f"flagnote-{flagnote_counter}",
                            "absolute_rotation": 0,
                        },
                    )
                    instances_list.add_unless_exists(
                        f"{instance.get('instance_name')}.leader",
                        {
                            "parent_csys_instance_name": current_affected_instance,
                            "parent_instance": instance.get("instance_name"),
                            "item_type": "flagnote-leader",
                            "location_is_node_or_segment": "Node",
                            "parent_csys_outputcsys_name": f"flagnote-leader-{flagnote_counter}",
                            "absolute_rotation": 0,
                            "cluster": instances_list.attribute_of(
                                instance.get("instance_name"), "cluster"
                            ),
                        },
                    )
                    flagnote_counter += 1
