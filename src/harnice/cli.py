import argparse
import os
import sys
import shutil
from harnice import state
from harnice.products import (
    device,
    harness,
    part,
    flagnote,
    tblock,
    system,
    disconnect,
    cable,
)


def ensure_cwd_exists():
    try:
        cwd = os.getcwd()
    except (FileNotFoundError, PermissionError):
        sys.exit(
            "Error: The current working directory is invalid "
            "(it may have been deleted or you lack permission to access it)."
        )

    if not os.path.exists(cwd):
        sys.exit(f"Error: The current working directory no longer exists: {cwd}")


def main():
    ensure_cwd_exists()

    parser = argparse.ArgumentParser(
        prog="harnice", description="Wire harness automation CLI"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "-r",
        "--render",
        choices=[
            "harness",
            "system",
            "part",
            "flagnote",
            "device",
            "disconnect",
            "tblock",
            "titleblock",
            "cable",
        ],
        help="Render a product type",
    )
    group.add_argument(
        "-l",
        "--lightweight",
        choices=["device"],
        help="Render a product type quickly without performing all checks",
    )
    group.add_argument(
        "--newrev",
        action="store_true",
        help="Create a new revision in the current working directory",
    )

    args = parser.parse_args()

    # Handle new revision creation
    if args.newrev:
        from harnice import fileio
        fileio.newrev()

    if args.render:
        render_map = {
            "harness": harness.render,
            "system": system.render,
            "part": part.render,
            "flagnote": flagnote.render,
            "device": device.render,
            "disconnect": disconnect.render,
            "cable": cable.render,
            "tblock": tblock.render,
            "titleblock": tblock.render,  # alias
        }
        render_map[args.render.lower()]()

    elif args.lightweight:
        device.lightweight_render()


def prompt(text, default=None):
    p = f"{text}"
    if default:
        p += f" [{default}]"
    p += ": "
    return input(p).strip() or default


def newrev():
    from harnice import fileio

    """
    Create a new revision directory by copying the current revision's contents
    and updating filenames to reflect the new revision number.
    """
    # Ensure revision structure is valid and get context
    fileio.verify_revision_structure()

    # Prompt user for new revision number
    new_rev_number = prompt(
        f"Current rev number: {fileio.partnumber('R')}. Enter new rev number:",
        default=str(int(fileio.partnumber("R")) + 1),
    )

    # Construct new revision directory path
    new_rev_dir = os.path.join(
        fileio.part_directory(), f"{fileio.partnumber('pn')}-rev{new_rev_number}"
    )

    # Ensure target directory does not already exist
    if os.path.exists(new_rev_dir):
        raise FileExistsError(f"Revision directory already exists: {new_rev_dir}")

    shutil.copytree(fileio.rev_directory(), new_rev_dir)

    # Walk the new directory and rename all files containing the old rev number
    for root, _, files in os.walk(new_rev_dir):
        for filename in files:
            new_suffix = f"rev{new_rev_number}"

            if fileio.partnumber("rev") in filename:
                old_path = os.path.join(root, filename)
                new_name = filename.replace(fileio.partnumber("rev"), new_suffix)
                new_path = os.path.join(root, new_name)

                os.rename(old_path, new_path)

    print(
        f"Successfully created new revision: {fileio.partnumber('pn-rev')}. Please cd into it."
    )
