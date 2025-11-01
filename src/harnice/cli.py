import argparse
import os
import sys
import shutil
from harnice.lists import rev_history
from harnice import state
from harnice import fileio

import_print_format = [
    "{:<8}",  # margin
    "{:<32}",  # instance_name column
    "{:<16}",  # item_type column
    "{:<16}",  # status column
    "{:<16}",  # import state column
]

def print_import_headers():
    print(f"{import_print_format[0].format('')}"
        f"{import_print_format[1].format('INSTANCE NAME')}"
        f"{import_print_format[2].format('ITEM TYPE')}"
        f"{import_print_format[3].format('LIBRARY STATUS')}"
        f"{import_print_format[4].format('IMPORT STATE')}"
    )

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

    group.add_argument(
        "-r", "--render",
        action="store_true",
        help="Render the product normally"
    )

    group.add_argument(
        "-l", "--lightweight",
        action="store_true",
        help="Render the product quickly without performing all checks"
    )

    group.add_argument("--newrev",
        action="store_true",
        help="Create a new revision in the current working directory")

    group.add_argument(
        "--gui",
        action="store_true",
        help="Launch the Harnice GUI launcher",
    )

    args = parser.parse_args()

    if args.gui:
        from harnice.gui.launcher import main as gui_main
        gui_main()
        return

    # -----------------------------
    # Handle new revision creation and exit
    # -----------------------------
    if args.newrev:
        newrev()
        return

    # -----------------------------
    # Ensure we are inside a revision folder
    # May change cwd if new PN created
    # -----------------------------
    fileio.verify_revision_structure()
    item_type = rev_history.info(field="product")

    # -----------------------------
    # Load product module
    # -----------------------------
    try:
        product_module = __import__(
            f"harnice.products.{item_type}",
            fromlist=[item_type]
        )
    except ModuleNotFoundError:
        sys.exit(f"Unknown product: '{item_type}'")

    # -----------------------------
    # Set the default fileio structure dict to the product's file_structure()
    # -----------------------------
    if hasattr(product_module, "file_structure"):
        structure = product_module.file_structure()
        state.set_file_structure(structure)
    else:
        sys.exit(f"Product '{item_type}' must define file_structure()")

    # -----------------------------
    # Generate product file structure
    # -----------------------------
    if hasattr(product_module, "generate_structure"):
        product_module.generate_structure()
    else:
        sys.exit(f"Product '{item_type}' must define generate_structure()")

    # -----------------------------
    # Execute render logic
    # -----------------------------
    if args.lightweight:
        try:
            product_module.render(lightweight=True)
        except TypeError:
            sys.exit(f"Product '{item_type}' does not support lightweight rendering")
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

def select_product_type():
    return prompt("What product type are you working on? (harness, system, device, etc.)", default="harness")