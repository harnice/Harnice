import argparse
import os
import sys
import shutil
from harnice import state
from harnice import fileio


def main():
    # Ensure cwd exists
    try:
        cwd = os.getcwd()
    except (FileNotFoundError, PermissionError):
        sys.exit(
            "Error: The current working directory is invalid "
            "(it may have been deleted or you lack permission to access it)."
        )

    if not os.path.exists(cwd):
        sys.exit(f"Error: The current working directory no longer exists: {cwd}")

    # -----------------------------
    # Argument parsing
    # -----------------------------
    parser = argparse.ArgumentParser(
        prog="harnice",
        description="Electrical system CAD",
    )

    group = parser.add_mutually_exclusive_group(required=True)

    group.add_argument("-r", "--render",
        help="Render a product type (e.g., harness, system, device, etc.)")

    group.add_argument("-l", "--lightweight",
        help="Render a product type quickly without performing all checks")

    group.add_argument("--newrev",
        action="store_true",
        help="Create a new revision in the current working directory")

    args = parser.parse_args()

    # -----------------------------
    # Handle new revision creation and exit
    # -----------------------------
    if args.newrev:
        newrev()
        return

    # -----------------------------
    # Determine product name from args
    # (This is now the single source of truth)
    # -----------------------------
    product_name = args.render or args.lightweight
    state.set_product(product_name)

    # -----------------------------
    # Ensure we are inside a revision folder
    # May change cwd if new PN created
    # -----------------------------
    fileio.verify_revision_structure()

    # -----------------------------
    # Load product module by name (general, no lists, no maintenance)
    # -----------------------------
    try:
        product_module = __import__(
            f"harnice.products.{product_name}",
            fromlist=[product_name]
        )
    except ModuleNotFoundError:
        sys.exit(f"Unknown product: '{product_name}'")

    if not hasattr(product_module, "render"):
        sys.exit(f"Product module '{product_name}' does not define render()")

    # -----------------------------
    # Execute render logic
    # -----------------------------
    if args.lightweight:
        try:
            product_module.render(lightweight=True)
        except TypeError:
            sys.exit(f"Product '{product_name}' does not support lightweight rendering")
    else:
        product_module.render()

    return


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
        f"Current rev number: {state.partnumber('R')}. Enter new rev number:",
        default=str(int(state.partnumber("R")) + 1),
    )

    # Construct new revision directory path
    new_rev_dir = os.path.join(
        fileio.part_directory(), f"{state.partnumber('pn')}-rev{new_rev_number}"
    )

    # Ensure target directory does not already exist
    if os.path.exists(new_rev_dir):
        raise FileExistsError(f"Revision directory already exists: {new_rev_dir}")

    shutil.copytree(fileio.rev_directory(), new_rev_dir)

    # Walk the new directory and rename all files containing the old rev number
    for root, _, files in os.walk(new_rev_dir):
        for filename in files:
            new_suffix = f"rev{new_rev_number}"

            if state.partnumber("rev") in filename:
                old_path = os.path.join(root, filename)
                new_name = filename.replace(state.partnumber("rev"), new_suffix)
                new_path = os.path.join(root, new_name)

                os.rename(old_path, new_path)

    print(
        f"Successfully created new revision: {state.partnumber('pn-rev')}. Please cd into it."
    )
