

# ===========================================================================
#                 pull harness definition from system
# ===========================================================================
system_pn = "{system_pn}" # enter your system part number
system_rev = "{system_rev}" # enter your system revision
system_base_directory = fileio.get_path_to_project(system_pn) # add the path to project_locations.csv in the root of harnice
system_target_net = "{target_net}" # enter the net you're building from

feature_tree_utils.run_macro(
    "import_harness_from_harnice_system",
    "harness_builder",
    "https://github.com/harnice/harnice",
    "harness-from-system-1",
    system_pn="{system_pn}",
    system_rev="{system_rev}",
    path_to_system_rev=os.path.join(
        system_base_directory,
        "{system_pn}-{system_rev}",
    ),
    target_net=system_target_net,
    manifest_nets=[system_target_net],
)

rev_history.overwrite(
    {{
        "desc": f"HARNESS '{{system_target_net}}' FROM SYSTEM '{{system_pn}}-{{system_rev}}'",
    }}
)

