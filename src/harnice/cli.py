import argparse
import os
import sys
import shutil
from harnice.lists import rev_history
from harnice import state
from harnice import fileio


def print_import_status(
    instance_name, item_type, library_status, import_state, called_from_base_directory
):
    print(
        f"{'':<4}"
        f"{instance_name:<40}"
        f"{item_type:<16}"
        f"{library_status:<16}"
        f"{import_state:<32}"
        f"{called_from_base_directory:<32}"
    )


def print_import_status_headers():
    print_import_status(
        "INSTANCE NAME",
        "ITEM TYPE",
        "LIBRARY STATUS",
        "IMPORT STATE",
        "CALLED FROM BASE DIRECTORY",
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
        "-r", "--render", action="store_true", help="Render the product normally"
    )

    group.add_argument(
        "-l",
        "--lightweight",
        action="store_true",
        help="Render the product quickly without performing all checks",
    )

    group.add_argument(
        "--newrev",
        action="store_true",
        help="Create a new revision in the current working directory",
    )

    group.add_argument(
        "--gui",
        action="store_true",
        help="Launch the feature tree editor",
    )

    group.add_argument(
        "--launcher",
        action="store_true",
        help="Launch the Harnice launcher window",
    )

    group.add_argument(
        "--graph-editor",
        action="store_true",
        help="Launch the formboard graph editor (harness product)",
    )

    group.add_argument(
        "--system-viewer",
        action="store_true",
        help="Launch the system viewer for this revision's lists (e.g. system product)",
    )

    args = parser.parse_args()

    if args.gui:
        _run_feature_tree_editor()
        return

    if args.launcher:
        from harnice.gui.launcher import main as gui_main

        gui_main()
        return

    if args.graph_editor:
        _run_graph_editor()
        return

    if args.system_viewer:
        _run_system_viewer()
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
            f"harnice.products.{item_type}", fromlist=[item_type]
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


def _run_feature_tree_editor():
    """Launch the feature tree editor (can be run from any directory)."""
    # Ensure function_index.json is up to date for the editor dropdowns
    from harnice.gui.build_feature_tree_gui import build as build_feature_index

    build_feature_index()

    from harnice.gui.feature_tree_server import run_server

    run_server(port=0, open_browser=True)


def _run_graph_editor():
    """Launch the formboard graph editor (must be run from a revision that has a formboard graph)."""
    fileio.verify_revision_structure()
    item_type = rev_history.info(field="product")

    try:
        product_module = __import__(
            f"harnice.products.{item_type}", fromlist=[item_type]
        )
    except ModuleNotFoundError:
        sys.exit(f"Unknown product: '{item_type}'")

    if hasattr(product_module, "file_structure"):
        structure = product_module.file_structure()
        state.set_file_structure(structure)
    else:
        sys.exit(f"Product '{item_type}' must define file_structure()")

    try:
        fileio.path("formboard graph definition")
    except TypeError:
        sys.exit(
            f"Product '{item_type}' does not have a formboard graph definition. "
            "The graph editor is only available for products that define one (e.g. harness)."
        )

    if hasattr(product_module, "generate_structure"):
        product_module.generate_structure()

    from harnice.gui.graph_editor_server import run_server

    run_server(port=0, open_browser=True)


def _run_system_viewer():
    """Launch the system viewer (must be run from a revision directory)."""
    fileio.verify_revision_structure()
    item_type = rev_history.info(field="product")

    try:
        product_module = __import__(
            f"harnice.products.{item_type}", fromlist=[item_type]
        )
    except ModuleNotFoundError:
        sys.exit(f"Unknown product: '{item_type}'")

    if hasattr(product_module, "file_structure"):
        structure = product_module.file_structure()
        state.set_file_structure(structure)
    else:
        sys.exit(f"Product '{item_type}' must define file_structure()")

    if hasattr(product_module, "generate_structure"):
        product_module.generate_structure()

    from harnice.gui.system_viewer_server import run_server

    run_server(port=0, open_browser=True)


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
        f"Successfully created new revision: {state.partnumber('pn')}-rev{new_rev_number}. Please cd into it."
    )


def select_product_type():
    from pathlib import Path
    import harnice.products as products_pkg
    from prompt_toolkit import prompt
    from prompt_toolkit.application.current import get_app
    from prompt_toolkit.completion import WordCompleter

    def get_product_types():
        products_dir = Path(products_pkg.__file__).parent
        all_types = sorted(
            p.stem for p in products_dir.glob("*.py") if p.name != "__init__.py"
        )
        priority = ["harness", "system", "device", "disconnect", "macro"]
        ordered = [p for p in priority if p in all_types]
        ordered += sorted(p for p in all_types if p not in priority)
        return ordered

    def show_completions_immediately():
        app = get_app()
        buf = app.current_buffer
        if buf.complete_state:
            buf.complete_next()
        else:
            buf.start_completion(select_first=False)

    product_types = get_product_types()
    product_map = {p.lower(): p for p in product_types}

    completer = WordCompleter(
        product_types,
        ignore_case=True,
        sentence=True,
    )

    while True:
        value = prompt(
            "Select product type: ",
            completer=completer,
            pre_run=show_completions_immediately,
        ).strip()

        if not value:
            continue

        key = value.lower()
        if key in product_map:
            return product_map[key]

        print(
            f"Unrecognized product type '{value}'. "
            f"Valid options: {', '.join(product_types)}"
        )
