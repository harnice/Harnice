from pathlib import Path
import docs_compiler
from harnice.lists import channel_map, circuits_list, disconnect_map, formboard_graph, instances_list, library_history, post_harness_instances_list, rev_history, signals_list, manifest

harnice_dir = Path(__file__).resolve().parents[1]
#========================================================
# CHANNEL MAPS
#========================================================
module_prefix = "channel_map"

md = ["""# Interacting with Channel Maps"""]
md.append("""\nA list of channels on devices within merged_nets that are either mapped to other channels or are unmapped.\n""")
md.append(docs_compiler.columns_header(module_prefix))
md.append(docs_compiler.columns_to_markdown(channel_map, "COLUMNS"))
md.append(docs_compiler.commands_header(module_prefix))
md.append(docs_compiler.print_function_docs(channel_map.new, module_prefix))
md.append(docs_compiler.print_function_docs(channel_map.map, module_prefix))
md.append(docs_compiler.print_function_docs(channel_map.already_mapped_set_append, module_prefix))
md.append(docs_compiler.print_function_docs(channel_map.already_mapped_set, module_prefix))
md.append(docs_compiler.print_function_docs(channel_map.already_mapped, module_prefix))

path = harnice_dir / "docs" / "interacting_with_data" / "channel_maps.md"
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text("".join(md), encoding="utf-8")

#========================================================
# CIRCUITS LISTS
#========================================================
module_prefix = "circuits_list"

md = ["""# Interacting with Circuits Lists"""]
md.append("""\nA list of every individual electrical connection that must be present in your system or harness to satisfy your channel and disconnect maps.\n""")
md.append(docs_compiler.columns_header(module_prefix))
md.append(docs_compiler.columns_to_markdown(circuits_list, "COLUMNS"))
md.append(docs_compiler.commands_header(module_prefix))
md.append(docs_compiler.print_function_docs(circuits_list.new, module_prefix))

path = harnice_dir / "docs" / "interacting_with_data" / "circuits_lists.md"
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text("".join(md), encoding="utf-8")

#========================================================
# DISCONNECT MAPS
#========================================================
module_prefix = "disconnect_map"

md = ["""# Interacting with Disconnect Maps"""]
md.append("""\nA list of every available channel on a every disconnect, and every channel that may or may not pass through it\n""")
md.append(docs_compiler.columns_header(module_prefix))
md.append(docs_compiler.columns_to_markdown(disconnect_map, "COLUMNS"))
md.append(docs_compiler.commands_header(module_prefix))
md.append(docs_compiler.print_function_docs(disconnect_map.new, module_prefix))
md.append(docs_compiler.print_function_docs(disconnect_map.assign, module_prefix))
md.append(docs_compiler.print_function_docs(disconnect_map.already_assigned_channels_through_disconnects_set_append, module_prefix))
md.append(docs_compiler.print_function_docs(disconnect_map.already_assigned_disconnects_set_append, module_prefix))
md.append(docs_compiler.print_function_docs(disconnect_map.already_assigned_channels_through_disconnects_set, module_prefix))
md.append(docs_compiler.print_function_docs(disconnect_map.already_assigned_disconnects_set, module_prefix))
md.append(docs_compiler.print_function_docs(disconnect_map.channel_is_already_assigned_through_disconnect, module_prefix))
md.append(docs_compiler.print_function_docs(disconnect_map.disconnect_is_already_assigned, module_prefix))
md.append(docs_compiler.print_function_docs(disconnect_map.ensure_requirements_met, module_prefix))

path = harnice_dir / "docs" / "interacting_with_data" / "disconnect_maps.md"
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text("".join(md), encoding="utf-8")

#========================================================
# FORMBOARD GRAPHS
#========================================================
module_prefix = "formboard_graph"

md = ["""# Interacting with Formboard Graphs"""]
md.append("""\nA table that describes the geometry of the formboard, and the nodes and segments that make up the formboard.\n""")
md.append(docs_compiler.columns_header(module_prefix))
md.append(docs_compiler.columns_to_markdown(formboard_graph, "COLUMNS"))
md.append(docs_compiler.commands_header(module_prefix))
md.append(docs_compiler.print_function_docs(formboard_graph.new, module_prefix))
md.append(docs_compiler.print_function_docs(formboard_graph.append, module_prefix))

path = harnice_dir / "docs" / "interacting_with_data" / "formboard_graphs.md"
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text("".join(md), encoding="utf-8")

#========================================================
# INSTANCES LISTS
#========================================================
module_prefix = "instances_list"

md = ["""## Interacting with Instances Lists"""]
md.append("""\nAn instances list is a list of every physical or notional item, idea, note, part, instruction, circuit, drawing element, thing, concept literally anything that describes how to build that harness or system.\n""")
md.append("""\nInstances lists are the single comprehensive source of truth for the product you are working on. Other documents like the Feature Tree, etc, build this list, and all output documentation are derived from it.\n""")
md.append(docs_compiler.columns_header(module_prefix))
md.append(docs_compiler.columns_to_markdown(instances_list, "COLUMNS"))
md.append(docs_compiler.commands_header(module_prefix))
md.append(docs_compiler.print_function_docs(instances_list.new_instance, module_prefix))
md.append(docs_compiler.print_function_docs(instances_list.modify, module_prefix))
md.append(docs_compiler.print_function_docs(instances_list.remove_instance, module_prefix))
md.append(docs_compiler.print_function_docs(instances_list.new, module_prefix))
md.append(docs_compiler.print_function_docs(instances_list.assign_bom_line_numbers, module_prefix))
md.append(docs_compiler.print_function_docs(instances_list.attribute_of, module_prefix))
md.append(docs_compiler.print_function_docs(instances_list.instance_in_connector_group_with_item_type, module_prefix))
md.append(docs_compiler.print_function_docs(instances_list.list_of_uniques, module_prefix))

path = harnice_dir / "docs" / "interacting_with_data" / "instances_lists.md"
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text("".join(md), encoding="utf-8")

#========================================================
# LIBRARY HISTORY
#========================================================
module_prefix = "library_history"

md = ["""# Interacting with Library History"""]
md.append("""\nA report of what was imported during the most recent render of the current product\n""")
md.append(docs_compiler.columns_header(module_prefix))
md.append(docs_compiler.columns_to_markdown(library_history, "COLUMNS"))
md.append(docs_compiler.commands_header(module_prefix))
md.append(docs_compiler.print_function_docs(library_history.new, module_prefix))
md.append(docs_compiler.print_function_docs(library_history.append, module_prefix))
path = harnice_dir / "docs" / "interacting_with_data" / "library_history.md"
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text("".join(md), encoding="utf-8")

#========================================================
# NETLISTS
#========================================================

md = ["""# Interacting with Netlists"""]
path = harnice_dir / "docs" / "interacting_with_data" / "netlists.md"
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text("".join(md), encoding="utf-8")

#========================================================
# POST-HARNESS INSTANCES LISTS
#========================================================

md = ["""# Interacting with Post Harness Instances Lists

A list of every physical or notional thing, drawing element, or concept that includes instances added at the harness level, that represents a system
"""]
md.append(docs_compiler.commands_header(module_prefix))
md.append(docs_compiler.print_function_docs(post_harness_instances_list.rebuild, module_prefix))
md.append(docs_compiler.print_function_docs(post_harness_instances_list.push, module_prefix))
path = harnice_dir / "docs" / "interacting_with_data" / "post_harness_instances_lists.md"
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text("".join(md), encoding="utf-8")

#========================================================
# REVISION HISTORY LISTS
#========================================================
module_prefix = "rev_history"

md = ["""# Interacting with Revision History Lists"""]
md.append("""\nA record of every revision of a part, and its release status\n""")
md.append(docs_compiler.columns_header(module_prefix))
md.append(docs_compiler.columns_to_markdown(rev_history, "COLUMNS"))
md.append(docs_compiler.commands_header(module_prefix))
md.append(docs_compiler.print_function_docs(rev_history.overwrite, module_prefix))
md.append(docs_compiler.print_function_docs(rev_history.info, module_prefix))
md.append(docs_compiler.print_function_docs(rev_history.initial_release_exists, module_prefix))
md.append(docs_compiler.print_function_docs(rev_history.initial_release_desc, module_prefix))
md.append(docs_compiler.print_function_docs(rev_history.update_datemodified, module_prefix))
md.append(docs_compiler.print_function_docs(rev_history.new, module_prefix))
md.append(docs_compiler.print_function_docs(rev_history.append, module_prefix))
path = harnice_dir / "docs" / "interacting_with_data" / "revision_history_lists.md"
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text("".join(md), encoding="utf-8")

#========================================================
# SIGNALS LISTS
#========================================================
module_prefix = "signals_list"

md = ["""# Interacting with Signals Lists"""]
md.append("""\nA Signals List is an exhaustive list of every signal is going into or out of a thing. Signals Lists are the primary way Harnice stores information about devices, and act as the source of truth for devices and disconnects.\n""")
md.append("\n---\n## Rules:\n")
md.append(r"""
 - Each signal is contained by one or more cavities of connectors

 - Each signal may be assigned to a functional signal of a channel, or left unused.

 - Every combination of (channel_id, signal) must be unique within the signals list
    - i.e. you can’t have two “ch1, pos” signals on the same device

 - Signals of channels in a signals list must agree with their channel type definitions
    - If a signal is on the list that has a channel name and a channel type, all of the required signals of that channel type must also be present in the list with the same channel name (you can't just define 'positive' if the channel type requires 'positive' and 'negative')

 - Every signal in the Signals List must have a pre-defined channel type

    ??? info "Channel Types"
        {% include-markdown "products/channel_type.md" %}

 - You can’t put signals of the same channel on different connectors
    - While this may sound inconvenient, it breaks a lot of internal assumptions Harnice is making on the back end about how to map channels. 

    - If you need to do this, I recommend the following two options:
    
        - **Most correct but confusing:** Define one channel type per signal, then manually chmap your channels or write a macro for mapping the channels to their respective destinations.

        - **Janky but easiest to understand:** Define a connector part number that actually represents multiple connectors, while using cavities to reference each connector.

 - “A” and “B” channels of the same disconnect must be compatible with each other""")
md.append(docs_compiler.columns_header(module_prefix))
md.append("### Columns of Signals Lists for Devices \n")
md.append(docs_compiler.columns_to_markdown(signals_list, "DEVICE_COLUMNS"))
md.append("### Columns of Signals Lists for Disconnects \n")
md.append(docs_compiler.columns_to_markdown(signals_list, "DISCONNECT_COLUMNS"))
md.append("\n\n---\n")
md.append(docs_compiler.commands_header(module_prefix))
md.append(docs_compiler.print_function_docs(signals_list.set_list_type, module_prefix))
md.append(docs_compiler.print_function_docs(signals_list.new, module_prefix))
md.append(docs_compiler.print_function_docs(signals_list.append, module_prefix))
md.append(docs_compiler.print_function_docs(signals_list.cavity_of_signal, module_prefix))
md.append(docs_compiler.print_function_docs(signals_list.connector_name_of_channel, module_prefix))
md.append("---\n")
path = harnice_dir / "docs" / "interacting_with_data" / "signals_lists.md"
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text("".join(md), encoding="utf-8")

#========================================================
# SYSTEM MANIFESTS
#========================================================
module_prefix = "manifest"

md = ["""# Interacting with System Manifests"""]
md.append("""\nA table that relates reference designator to part number(s), and may contain other information indexed to the reference designator\n""")
md.append(docs_compiler.columns_header(module_prefix))
md.append(docs_compiler.columns_to_markdown(manifest, "COLUMNS"))
md.append(docs_compiler.commands_header(module_prefix))
md.append(docs_compiler.print_function_docs(manifest.new, module_prefix))
md.append(docs_compiler.print_function_docs(manifest.update_upstream, module_prefix))
md.append(docs_compiler.print_function_docs(manifest.new, module_prefix))
md.append(docs_compiler.print_function_docs(manifest.update_upstream, module_prefix))
path = harnice_dir / "docs" / "interacting_with_data" / "system_manifests.md"
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text("".join(md), encoding="utf-8")