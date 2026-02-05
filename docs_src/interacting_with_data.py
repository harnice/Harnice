import docs_functions
from harnice.lists import (
    channel_map,
    circuits_list,
    disconnect_map,
    formboard_graph,
    instances_list,
    library_history,
    post_harness_instances_list,
    rev_history,
    signals_list,
    manifest,
)


def main():
    # ========================================================
    # CHANNEL MAPS
    # ========================================================
    module_prefix = "channel_map"

    md = ["""# Interacting with Channel Maps"""]
    md.append(
        """\nA list of channels on devices within merged_nets that are either mapped to other channels or are unmapped.\n"""
    )
    md.append(docs_functions.columns_header(module_prefix))
    md.append(docs_functions.columns_to_markdown(channel_map, "COLUMNS"))
    md.append(docs_functions.commands_header(module_prefix))
    md.append(docs_functions.print_function_docs(channel_map.new, module_prefix))
    md.append(docs_functions.print_function_docs(channel_map.map, module_prefix))
    md.append(
        docs_functions.print_function_docs(
            channel_map.already_mapped_set_append, module_prefix
        )
    )
    md.append(
        docs_functions.print_function_docs(
            channel_map.already_mapped_set, module_prefix
        )
    )
    md.append(
        docs_functions.print_function_docs(channel_map.already_mapped, module_prefix)
    )

    path = (
        docs_functions.harnice_dir()
        / "docs"
        / "interacting_with_data"
        / "_channel_maps.md"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(md), encoding="utf-8")

    # ========================================================
    # CIRCUITS LISTS
    # ========================================================
    module_prefix = "circuits_list"

    md = ["""# Interacting with Circuits Lists"""]
    md.append(
        """\nA list of every individual electrical connection that must be present in your system or harness to satisfy your channel and disconnect maps.\n"""
    )
    md.append(docs_functions.columns_header(module_prefix))
    md.append(docs_functions.columns_to_markdown(circuits_list, "COLUMNS"))
    md.append(docs_functions.commands_header(module_prefix))
    md.append(docs_functions.print_function_docs(circuits_list.new, module_prefix))

    path = (
        docs_functions.harnice_dir()
        / "docs"
        / "interacting_with_data"
        / "_circuits_lists.md"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(md), encoding="utf-8")

    # ========================================================
    # DISCONNECT MAPS
    # ========================================================
    module_prefix = "disconnect_map"

    md = ["""# Interacting with Disconnect Maps"""]
    md.append(
        """\nA list of every available channel on a every disconnect, and every channel that may or may not pass through it\n"""
    )
    md.append(docs_functions.columns_header(module_prefix))
    md.append(docs_functions.columns_to_markdown(disconnect_map, "COLUMNS"))
    md.append(docs_functions.commands_header(module_prefix))
    md.append(docs_functions.print_function_docs(disconnect_map.new, module_prefix))
    md.append(docs_functions.print_function_docs(disconnect_map.assign, module_prefix))
    md.append(
        docs_functions.print_function_docs(
            disconnect_map.already_assigned_channels_through_disconnects_set_append,
            module_prefix,
        )
    )
    md.append(
        docs_functions.print_function_docs(
            disconnect_map.already_assigned_disconnects_set_append, module_prefix
        )
    )
    md.append(
        docs_functions.print_function_docs(
            disconnect_map.already_assigned_channels_through_disconnects_set,
            module_prefix,
        )
    )
    md.append(
        docs_functions.print_function_docs(
            disconnect_map.already_assigned_disconnects_set, module_prefix
        )
    )
    md.append(
        docs_functions.print_function_docs(
            disconnect_map.channel_is_already_assigned_through_disconnect, module_prefix
        )
    )
    md.append(
        docs_functions.print_function_docs(
            disconnect_map.disconnect_is_already_assigned, module_prefix
        )
    )
    md.append(
        docs_functions.print_function_docs(
            disconnect_map.ensure_requirements_met, module_prefix
        )
    )

    path = (
        docs_functions.harnice_dir()
        / "docs"
        / "interacting_with_data"
        / "_disconnect_maps.md"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(md), encoding="utf-8")

    # ========================================================
    # FORMBOARD GRAPHS
    # ========================================================
    module_prefix = "formboard_graph"

    md = ["""# Interacting with Formboard Graphs"""]
    md.append(
        """\nA table that describes the geometry of the formboard, and the nodes and segments that make up the formboard.\n"""
    )
    md.append(docs_functions.columns_header(module_prefix))
    md.append(docs_functions.columns_to_markdown(formboard_graph, "COLUMNS"))
    md.append(docs_functions.commands_header(module_prefix))
    md.append(docs_functions.print_function_docs(formboard_graph.new, module_prefix))
    md.append(docs_functions.print_function_docs(formboard_graph.append, module_prefix))

    path = (
        docs_functions.harnice_dir()
        / "docs"
        / "interacting_with_data"
        / "_formboard_graphs.md"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(md), encoding="utf-8")

    # ========================================================
    # INSTANCES LISTS
    # ========================================================
    module_prefix = "instances_list"

    md = ["""## Interacting with Instances Lists"""]
    md.append(
        """\nAn instances list is a list of every physical or notional item, idea, note, part, instruction, circuit, drawing element, thing, concept literally anything that describes how to build that harness or system.\n"""
    )
    md.append(
        """\nInstances lists are the single comprehensive source of truth for the product you are working on. Other documents like the Feature Tree, etc, build this list, and all output documentation are derived from it.\n"""
    )
    md.append(docs_functions.columns_header(module_prefix))
    md.append(docs_functions.columns_to_markdown(instances_list, "COLUMNS"))
    md.append(docs_functions.commands_header(module_prefix))
    md.append(
        docs_functions.print_function_docs(instances_list.new_instance, module_prefix)
    )
    md.append(docs_functions.print_function_docs(instances_list.modify, module_prefix))
    md.append(
        docs_functions.print_function_docs(
            instances_list.remove_instance, module_prefix
        )
    )
    md.append(docs_functions.print_function_docs(instances_list.new, module_prefix))
    md.append(
        docs_functions.print_function_docs(
            instances_list.assign_bom_line_numbers, module_prefix
        )
    )
    md.append(
        docs_functions.print_function_docs(instances_list.attribute_of, module_prefix)
    )
    md.append(
        docs_functions.print_function_docs(
            instances_list.instance_in_connector_group_with_item_type, module_prefix
        )
    )
    md.append(
        docs_functions.print_function_docs(
            instances_list.list_of_uniques, module_prefix
        )
    )

    path = (
        docs_functions.harnice_dir()
        / "docs"
        / "interacting_with_data"
        / "_instances_lists.md"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(md), encoding="utf-8")

    # ========================================================
    # LIBRARY HISTORY
    # ========================================================
    module_prefix = "library_history"

    md = ["""# Interacting with Library History"""]
    md.append(
        """\nA report of what was imported during the most recent render of the current product\n"""
    )
    md.append(docs_functions.columns_header(module_prefix))
    md.append(docs_functions.columns_to_markdown(library_history, "COLUMNS"))
    md.append(docs_functions.commands_header(module_prefix))
    md.append(docs_functions.print_function_docs(library_history.new, module_prefix))
    md.append(docs_functions.print_function_docs(library_history.append, module_prefix))
    path = (
        docs_functions.harnice_dir()
        / "docs"
        / "interacting_with_data"
        / "_library_history.md"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(md), encoding="utf-8")

    # ========================================================
    # NETLISTS
    # ========================================================

    md = ["""# Interacting with Netlists"""]
    path = (
        docs_functions.harnice_dir() / "docs" / "interacting_with_data" / "_netlists.md"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(md), encoding="utf-8")

    # ========================================================
    # POST-HARNESS INSTANCES LISTS
    # ========================================================

    md = [
        """# Interacting with Post Harness Instances Lists

A list of every physical or notional thing, drawing element, or concept that includes instances added at the harness level, that represents a system
"""
    ]
    md.append(docs_functions.commands_header(module_prefix))
    md.append(
        docs_functions.print_function_docs(
            post_harness_instances_list.rebuild, module_prefix
        )
    )
    md.append(
        docs_functions.print_function_docs(
            post_harness_instances_list.push, module_prefix
        )
    )
    path = (
        docs_functions.harnice_dir()
        / "docs"
        / "interacting_with_data"
        / "_post_harness_instances_lists.md"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(md), encoding="utf-8")

    # ========================================================
    # REVISION HISTORY LISTS
    # ========================================================
    module_prefix = "rev_history"

    md = ["""# Interacting with Revision History Lists"""]
    md.append("""\nA record of every revision of a part, and its release status\n""")
    md.append(docs_functions.columns_header(module_prefix))
    md.append(docs_functions.columns_to_markdown(rev_history, "COLUMNS"))
    md.append(docs_functions.commands_header(module_prefix))
    md.append(docs_functions.print_function_docs(rev_history.overwrite, module_prefix))
    md.append(docs_functions.print_function_docs(rev_history.info, module_prefix))
    md.append(
        docs_functions.print_function_docs(
            rev_history.initial_release_exists, module_prefix
        )
    )
    md.append(
        docs_functions.print_function_docs(
            rev_history.initial_release_desc, module_prefix
        )
    )
    md.append(
        docs_functions.print_function_docs(
            rev_history.update_datemodified, module_prefix
        )
    )
    md.append(docs_functions.print_function_docs(rev_history.new, module_prefix))
    md.append(docs_functions.print_function_docs(rev_history.append, module_prefix))
    md.append(docs_functions.print_function_docs(rev_history.part_family_append, module_prefix))
    path = (
        docs_functions.harnice_dir()
        / "docs"
        / "interacting_with_data"
        / "_revision_history_lists.md"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(md), encoding="utf-8")

    # ========================================================
    # SIGNALS LISTS
    # ========================================================
    module_prefix = "signals_list"

    md = ["""# Interacting with Signals Lists"""]
    md.append(
        """\nA Signals List is an exhaustive list of every signal is going into or out of a thing. Signals Lists are the primary way Harnice stores information about devices, and act as the source of truth for devices and disconnects.\n"""
    )
    md.append(
        "\n---\n## Signals List Validation Checks:\n*(These are automatically validated when you render the device or disconnect that owns the list.)*\n\n"
    )
    md.append("""{% include-markdown "fragments/signals_list_requirements.md" %}""")
    md.append(docs_functions.columns_header(module_prefix))
    md.append("### Columns of Signals Lists for Devices \n")
    md.append(docs_functions.columns_to_markdown(signals_list, "DEVICE_COLUMNS"))
    md.append("### Columns of Signals Lists for Disconnects \n")
    md.append(docs_functions.columns_to_markdown(signals_list, "DISCONNECT_COLUMNS"))
    md.append("\n\n---\n")
    md.append(docs_functions.commands_header(module_prefix))
    md.append(
        docs_functions.print_function_docs(signals_list.set_list_type, module_prefix)
    )
    md.append(docs_functions.print_function_docs(signals_list.new, module_prefix))
    md.append(docs_functions.print_function_docs(signals_list.append, module_prefix))
    md.append(
        docs_functions.print_function_docs(signals_list.cavity_of_signal, module_prefix)
    )
    md.append(
        docs_functions.print_function_docs(
            signals_list.connector_name_of_channel, module_prefix
        )
    )
    md.append("---\n")
    path = (
        docs_functions.harnice_dir()
        / "docs"
        / "interacting_with_data"
        / "_signals_lists.md"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(md), encoding="utf-8")

    # ========================================================
    # SYSTEM MANIFESTS
    # ========================================================
    module_prefix = "manifest"

    md = ["""# Interacting with System Manifests"""]
    md.append(
        """\nA table that relates reference designator to part number(s), and may contain other information indexed to the reference designator\n"""
    )
    md.append(docs_functions.columns_header(module_prefix))
    md.append(docs_functions.columns_to_markdown(manifest, "COLUMNS"))
    md.append(docs_functions.commands_header(module_prefix))
    md.append(docs_functions.print_function_docs(manifest.new, module_prefix))
    md.append(
        docs_functions.print_function_docs(manifest.update_upstream, module_prefix)
    )
    md.append(docs_functions.print_function_docs(manifest.new, module_prefix))
    md.append(
        docs_functions.print_function_docs(manifest.update_upstream, module_prefix)
    )
    path = (
        docs_functions.harnice_dir()
        / "docs"
        / "interacting_with_data"
        / "_system_manifests.md"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(md), encoding="utf-8")
