import runpy
import os
from harnice import fileio, cli, state
from harnice.lists import instances_list, library_history
from harnice.utils import feature_tree_utils

# History file in Harnice repo root: rows of (system name, revision), most recent first
_HARNESS_SYSTEM_HISTORY_FILENAME = ".harness_system_references"

default_desc = "HARNESS, DOES A FOR B"


def _system_ref_history_path():
    """Path to the persisted system name / revision history file (in repo root)."""
    return os.path.join(fileio.harnice_root(), _HARNESS_SYSTEM_HISTORY_FILENAME)


def _load_system_ref_history():
    """Load list of (system_name, revision) from repo root, most recent first. Returns [] if missing/invalid."""
    path = _system_ref_history_path()
    if not os.path.exists(path):
        return []
    out = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split("\t", 1)
            if len(parts) == 2:
                out.append((parts[0].strip(), parts[1].strip()))
    return out


def _save_system_ref_history(history):
    """Write list of (system_name, revision) to repo root, most recent first."""
    path = _system_ref_history_path()
    with open(path, "w", encoding="utf-8") as f:
        for system_name, revision in history:
            f.write(f"{system_name}\t{revision}\n")


def _revision_for_system_name(history, system_name):
    """Return the revision stored with this system name (first/match = most recent), or last-used rev."""
    for sn, rev in history:
        if sn == system_name:
            return rev
    return history[0][1] if history else ""


def _prompt_system_pn_rev():
    """Prompt for system name (Tab cycles history) then revision (auto-filled from selection). Returns (system_pn, system_rev)."""
    history = _load_system_ref_history()
    if not history:
        system_pn = cli.prompt("Enter the system part number")
        system_rev = cli.prompt("Enter the system revision id (ex. rev1)")
        if system_pn and system_rev:
            _save_system_ref_history([(system_pn, system_rev)])
        return system_pn, system_rev

    from prompt_toolkit import prompt as pt_prompt
    from prompt_toolkit.key_binding import KeyBindings

    # Tab cycles through system names only; each entry has an associated revision for the second prompt
    system_names = [sn for sn, _ in history]
    current_index = [0]

    def get_current_system_name():
        return system_names[current_index[0]]

    kb = KeyBindings()

    @kb.add("tab")
    def _(event):
        current_index[0] = (current_index[0] + 1) % len(system_names)
        event.app.current_buffer.text = get_current_system_name()

    @kb.add("s-tab")
    def _(event):
        current_index[0] = (current_index[0] - 1) % len(system_names)
        event.app.current_buffer.text = get_current_system_name()

    prompt_message = "Enter the system part number (Tab to cycle previous): "
    initial = get_current_system_name()
    system_pn = pt_prompt(
        prompt_message,
        default=initial,
        key_bindings=kb,
    ).strip()
    if not system_pn:
        system_pn = get_current_system_name()

    # Revision is cued from the selected system name (no Tab cycling on rev)
    suggested_rev = _revision_for_system_name(history, system_pn)
    system_rev = cli.prompt(
        "Enter the system revision id (ex. rev1)",
        default=suggested_rev,
    )
    system_rev = (system_rev or suggested_rev).strip()

    _prepend_and_save(history, system_pn, system_rev)
    return system_pn, system_rev


def _prepend_and_save(history, system_name, revision):
    """Prepend (system_name, revision) to history (avoid duplicate at front), keep finite size, save."""
    new = [(system_name, revision)]
    rest = [(s, r) for s, r in history if (s, r) != (system_name, revision)]
    _save_system_ref_history((new + rest)[:50])


documentation_description = "A harness is an assembly of connectors, cables, and other electrical components that connect multiple devices together. It is the physical item that is built and installed in a system."


def file_structure():
    return {
        f"{state.partnumber('pn-rev')}-feature_tree.py": "feature tree",
        f"{state.partnumber('pn-rev')}-instances_list.tsv": "instances list",
        f"{state.partnumber('pn-rev')}-formboard_graph_definition.png": "formboard graph definition png",
        f"{state.partnumber('pn-rev')}-library_import_history.tsv": "library history",
        "interactive_files": {
            f"{state.partnumber('pn-rev')}.formboard_graph_definition.tsv": "formboard graph definition",
        },
    }


def generate_structure():
    os.makedirs(
        fileio.dirpath("interactive_files", structure_dict=file_structure()),
        exist_ok=True,
    )


def render():
    # ======================================================================
    # 1. Feature tree does not exist: prompt user and create it
    # ======================================================================
    if not os.path.exists(fileio.path("feature tree", structure_dict=file_structure())):
        # ------------------------------------------------------------------
        # Ask whether this harness pulls from a system or not
        # ------------------------------------------------------------------
        print(
            "  's'   Enter 's' for system (or just hit enter) "
            "if this harness is pulling data from a system instances list"
        )
        print(
            "  'n'   Enter 'n' for none to build your harness entirely "
            "out of rules in feature tree (you're hardcore)"
        )
        build_macro = cli.prompt("")

        # ------------------------------------------------------------------
        # If harness is built from a system, ask for system parameters
        # ------------------------------------------------------------------
        if build_macro in (None, "", "s"):
            system_pn, system_rev = _prompt_system_pn_rev()
            target_net = cli.prompt("Enter the net you want to build this harness from (kicad nets start with a forward slash)")

            # Inject actual values into template
            build_macro_block = feature_tree_utils.default_feature_tree_contents(
                "harness_default_build_macro_block.py",
                replacements={
                    "system_part_number": system_pn,
                    "system_revision": system_rev,
                    "target_net": target_net,
                },
            )
            push_block = feature_tree_utils.default_feature_tree_contents(
                "harness_default_push_block.py"
            )
        # ------------------------------------------------------------------
        # Hardcore mode — no system importing
        # ------------------------------------------------------------------
        elif build_macro == "n":
            build_macro_block = ""
            push_block = ""

        else:
            print(
                "Unrecognized input. If you meant to select a template not listed, "
                "just select a template, delete the contents and start over manually. rip."
            )
            exit()

        # ------------------------------------------------------------------
        # Write feature tree file
        # ------------------------------------------------------------------
        feature_tree_text = feature_tree_utils.default_feature_tree_contents(
            "harness_default_feature_tree.py",
            {
                "build_macro_block": build_macro_block,
                "push_block": push_block,
            },
        )

        with open(fileio.path("feature tree"), "w", encoding="utf-8") as f:
            f.write(feature_tree_text)

    # ======================================================================
    # 2. Init library + instances list
    # ======================================================================
    library_history.new()
    instances_list.new()
    instances_list.new_instance(
        "origin",
        {
            "instance_name": "origin",
            "item_type": "origin",
            "location_type": "node",
        },
    )

    # ======================================================================
    # 3. Run the feature tree
    # ======================================================================
    cli.print_import_status_headers()
    runpy.run_path(fileio.path("feature tree"), run_name="__main__")

    print(f"Harnice: harness {state.partnumber('pn')} rendered successfully!\n")
