"""
feature_tree_ribbon_spec.py
Manual specification for the feature tree code editor ribbon.
- Defines which functions are scraped (only those listed)
- Defines organization: groups -> sub-groups -> functions
- Independent of source code layout
"""

# Module alias -> filesystem path (relative to harnice root)
MODULE_PATHS = {
    "available_network": "lists/available_network.py",
    "channel_map": "lists/channel_map.py",
    "chosen_network": "lists/chosen_network.py",
    "circuits_list": "lists/circuits_list.py",
    "disconnect_map": "lists/disconnect_map.py",
    "flattened_network": "lists/flattened_network.py",
    "instances_list": "lists/instances_list.py",
    "library_history": "lists/library_history.py",
    "manifest": "lists/manifest.py",
    "post_harness_instances_list": "lists/post_harness_instances_list.py",
    "rev_history": "lists/rev_history.py",
    "signals_list": "lists/signals_list.py",
    "appearance": "utils/appearance.py",
    "circuit_utils": "utils/circuit_utils.py",
    "feature_tree_utils": "utils/feature_tree_utils.py",
    "library_utils": "utils/library_utils.py",
    "note_utils": "utils/note_utils.py",
    "svg_utils": "utils/svg_utils.py",
    "system_utils": "utils/system_utils.py",
    "fileio": "fileio.py",
    "state": "state.py",
}

# Recursive structure:
# - dict: group label -> sub-dict or list of function refs
# - list: flat list of function refs
# - function ref: ("module_alias", "function_name")
FEATURE_TREE_SPEC = {
    "Instances List": [
        ("instances_list", "new"),
        ("instances_list", "new_instance"),
        ("instances_list", "remove_instance"),
        ("instances_list", "modify"),
        ("instances_list", "attribute_of"),
        ("instances_list", "list_of_uniques"),
        ("instances_list", "instance_in_connector_group_with_item_type"),
        ("instances_list", "assign_bom_line_numbers"),
    ],
    "Bundle Networks": {
        "Available Network": [
            ("available_network", "read"),
            ("available_network", "write"),
            ("available_network", "verify"),
        ],
        "Chosen Network": [
            ("chosen_network", "build_chosen_network"),
            ("chosen_network", "read_available_network"),
            ("chosen_network", "resolve_chosen_network"),
            ("chosen_network", "write_chosen_network"),
        ],
        "Flattened Network": [
            ("flattened_network", "build_flattened_network"),
            ("flattened_network", "read_chosen_network"),
            ("flattened_network", "read_flattened_network"),
            ("flattened_network", "write_flattened_network"),
        ],
    },
    "Channels and Mapping": {
        "Channel Map": [
            ("channel_map", "new"),
            ("channel_map", "map"),
            ("channel_map", "already_mapped"),
            ("channel_map", "already_mapped_set"),
            ("channel_map", "already_mapped_set_append"),
        ],
        "Disconnect Map": [
            ("disconnect_map", "new"),
            ("disconnect_map", "assign"),
            ("disconnect_map", "disconnect_is_already_assigned"),
            ("disconnect_map", "channel_is_already_assigned_through_disconnect"),
            ("disconnect_map", "already_assigned_disconnects_set"),
            ("disconnect_map", "already_assigned_disconnects_set_append"),
            ("disconnect_map", "already_assigned_channels_through_disconnects_set"),
            (
                "disconnect_map",
                "already_assigned_channels_through_disconnects_set_append",
            ),
            ("disconnect_map", "ensure_requirements_met"),
        ],
    },
    "Electrical": {
        "Circuits": [
            ("circuits_list", "new"),
        ],
        "Signals": [
            ("signals_list", "new"),
            ("signals_list", "append"),
            ("signals_list", "cavity_of_signal"),
            ("signals_list", "connector_name_of_channel"),
        ],
    },
    "Revision History": {
        "Revision History": [
            ("rev_history", "new"),
            ("rev_history", "append"),
            ("rev_history", "overwrite"),
            ("rev_history", "info"),
            ("rev_history", "initial_release_exists"),
            ("rev_history", "initial_release_desc"),
            ("rev_history", "part_family_append"),
            ("rev_history", "update_datemodified"),
        ],
    },
    "Feature Tree Tools": {
        "General": [
            ("feature_tree_utils", "run_feature_for_relative"),
            ("feature_tree_utils", "lookup_outputcsys_from_lib_used"),
        ],
        "Macros": [
            ("feature_tree_utils", "run_macro"),
        ],
        "Part Libraries": [
            ("library_utils", "pull"),
            ("library_utils", "get_local_path"),
        ],
        "Part Library History": [
            ("library_history", "new"),
            ("library_history", "append"),
        ],
    },
    "Build Notes": {
        "General": [
            ("note_utils", "new_note"),
            ("note_utils", "combine_notes"),
            ("note_utils", "parse_note_instance"),
            ("note_utils", "assign_buildnote_numbers"),
            ("note_utils", "get_lib_build_notes"),
            ("note_utils", "get_lib_tools"),
            ("note_utils", "make_bom_flagnote"),
            ("note_utils", "make_buildnote_flagnote"),
            ("note_utils", "make_part_name_flagnote"),
            ("note_utils", "make_rev_change_flagnote"),
            ("note_utils", "make_rev_history_notes"),
        ],
    },
    "Utils": {
        "SVG": [
            ("svg_utils", "add_entire_svg_file_contents_to_group"),
            ("svg_utils", "draw_styled_path"),
            ("svg_utils", "find_and_replace_svg_group"),
            ("svg_utils", "table"),
        ],
        "Appearance": [
            ("appearance", "parse"),
        ],
    },
    "System": {
        "General": [
            ("system_utils", "make_instances_from_bom"),
            (
                "system_utils",
                "make_instances_for_connectors_cavities_nodes_channels_circuits",
            ),
            ("system_utils", "add_chains_to_channel_map"),
            ("system_utils", "connector_of_channel"),
            ("system_utils", "find_connector_with_no_circuit"),
            ("system_utils", "mpn_of_device_refdes"),
        ],
        "Manifest": [
            ("manifest", "new"),
            ("manifest", "update_upstream"),
        ],
        "Post-Harness Instances": [
            ("post_harness_instances_list", "rebuild"),
            ("post_harness_instances_list", "push"),
        ],
    },
    "Files and State": {
        "Current State": [
            ("state", "partnumber"),
            ("state", "set_pn"),
            ("state", "set_rev"),
            ("state", "set_product"),
            ("state", "set_net"),
            ("state", "set_file_structure"),
        ],
        "Finding Files": [
            ("fileio", "dirpath"),
            ("fileio", "part_directory"),
            ("fileio", "rev_directory"),
            ("fileio", "read_tsv"),
            ("fileio", "verify_revision_structure"),
            ("fileio", "get_path_to_project"),
            ("fileio", "harnice_root"),
            ("fileio", "drawnby"),
            ("fileio", "today"),
        ],
        "Commands": [
            ("feature_tree_utils", "copy_pdfs_to_cwd"),
            ("fileio", "silentremove"),
            ("fileio", "get_git_hash_of_harnice_src"),
        ],
    },
}
