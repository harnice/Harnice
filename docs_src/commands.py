import docs_compiler
from harnice.utils import feature_tree_utils, library_utils, circuit_utils, formboard_utils, note_utils, svg_utils, system_utils, appearance

#========================================================
# LIBRARY UTILS
#========================================================
module_prefix = "library_utils"

md = ["# Library Utilities"]
md.append(docs_compiler.commands_header(module_prefix))
md.append(docs_compiler.print_function_docs(library_utils.pull, module_prefix))
md.append(docs_compiler.print_function_docs(library_utils.get_local_path, module_prefix))

path = docs_compiler.harnice_dir() / "docs" / "commands" / "library_utils.md"
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text("".join(md), encoding="utf-8")

#========================================================
# CIRCUIT UTILS
#========================================================
module_prefix = "circuit_utils"

md = ["# Circuit Utilities"]
md.append(docs_compiler.commands_header(module_prefix))
md.append(docs_compiler.print_function_docs(circuit_utils.end_ports_of_circuit, module_prefix))
md.append(docs_compiler.print_function_docs(circuit_utils.max_port_number_in_circuit, module_prefix))
md.append(docs_compiler.print_function_docs(circuit_utils.squeeze_instance_between_ports_in_circuit, module_prefix))
md.append(docs_compiler.print_function_docs(circuit_utils.instances_of_circuit, module_prefix))
md.append(docs_compiler.print_function_docs(circuit_utils.instance_of_circuit_port_number, module_prefix))
md.append(docs_compiler.print_function_docs(circuit_utils.circuit_instance_of_instance, module_prefix))
md.append(docs_compiler.print_function_docs(circuit_utils.assign_cable_conductor, module_prefix))
path = docs_compiler.harnice_dir() / "docs" / "commands" / "circuits_utils.md"
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text("".join(md), encoding="utf-8")

#========================================================
# FEATURE TREE UTILS
#========================================================
module_prefix = "feature_tree_utils"

md = ["# Feature Tree Utilities"]
md.append(docs_compiler.commands_header(module_prefix))
md.append(docs_compiler.print_function_docs(feature_tree_utils.run_macro, module_prefix))
md.append(docs_compiler.print_function_docs(feature_tree_utils.lookup_outputcsys_from_lib_used, module_prefix))
md.append(docs_compiler.print_function_docs(feature_tree_utils.copy_pdfs_to_cwd, module_prefix))
md.append(docs_compiler.print_function_docs(feature_tree_utils.run_feature_for_relative, module_prefix))

path = docs_compiler.harnice_dir() / "docs" / "commands" / "feature_tree_utils.md"
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text("".join(md), encoding="utf-8")

#========================================================
# FORMBOARD UTILS
#========================================================
module_prefix = "formboard_utils"
md = ["# Formboard Utilities"]
md.append(docs_compiler.commands_header(module_prefix))
md.append(docs_compiler.print_function_docs(formboard_utils.validate_nodes, module_prefix))
md.append(docs_compiler.print_function_docs(formboard_utils.map_instance_to_segments, module_prefix))
md.append(docs_compiler.print_function_docs(formboard_utils.calculate_location, module_prefix))
md.append(docs_compiler.print_function_docs(formboard_utils.draw_line, module_prefix))

path = docs_compiler.harnice_dir() / "docs" / "commands" / "formboard_utils.md"
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text("".join(md), encoding="utf-8")


#========================================================
# NOTE UTILS
#========================================================

module_prefix = "note_utils"
md = ["# Note Utilities"]
md.append(docs_compiler.commands_header(module_prefix))
md.append(docs_compiler.print_function_docs(note_utils.new_note, module_prefix))
md.append(docs_compiler.print_function_docs(note_utils.assign_buildnote_numbers, module_prefix))
md.append(docs_compiler.print_function_docs(note_utils.make_rev_history_notes, module_prefix))
md.append(docs_compiler.print_function_docs(note_utils.make_bom_flagnote, module_prefix))
md.append(docs_compiler.print_function_docs(note_utils.make_part_name_flagnote, module_prefix))
md.append(docs_compiler.print_function_docs(note_utils.make_buildnote_flagnote, module_prefix))
md.append(docs_compiler.print_function_docs(note_utils.make_rev_change_flagnote, module_prefix))
md.append(docs_compiler.print_function_docs(note_utils.parse_note_instance, module_prefix))
md.append(docs_compiler.print_function_docs(note_utils.get_lib_build_notes, module_prefix))
md.append(docs_compiler.print_function_docs(note_utils.get_lib_tools, module_prefix))
md.append(docs_compiler.print_function_docs(note_utils.combine_notes, module_prefix))

path = docs_compiler.harnice_dir() / "docs" / "commands" / "note_utils.md"
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text("".join(md), encoding="utf-8")


#========================================================
# SVG UTILS
#========================================================
module_prefix = "svg_utils"

md = ["# SVG Utilities"]
md.append(docs_compiler.commands_header(module_prefix))
md.append(docs_compiler.print_function_docs(svg_utils.table, module_prefix))
md.append(docs_compiler.print_function_docs(svg_utils.add_entire_svg_file_contents_to_group, module_prefix))
md.append(docs_compiler.print_function_docs(svg_utils.find_and_replace_svg_group, module_prefix))
md.append(docs_compiler.print_function_docs(svg_utils.draw_styled_path, module_prefix))

path = docs_compiler.harnice_dir() / "docs" / "commands" / "svg_utils.md"
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text("".join(md), encoding="utf-8")

#========================================================
# SYSTEM UTILS
#========================================================
module_prefix = "system_utils"
md = ["# System Utilities"]
md.append(docs_compiler.commands_header(module_prefix))
md.append(docs_compiler.print_function_docs(system_utils.mpn_of_device_refdes, module_prefix))
md.append(docs_compiler.print_function_docs(system_utils.connector_of_channel, module_prefix))
md.append(docs_compiler.print_function_docs(system_utils.find_connector_with_no_circuit, module_prefix))
md.append(docs_compiler.print_function_docs(system_utils.make_instances_for_connectors_cavities_nodes_channels_circuits, module_prefix))
md.append(docs_compiler.print_function_docs(system_utils.add_chains_to_channel_map, module_prefix))
md.append(docs_compiler.print_function_docs(system_utils.make_instances_from_bom, module_prefix))

path = docs_compiler.harnice_dir() / "docs" / "commands" / "system_utils.md"
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text("".join(md), encoding="utf-8")


#========================================================
# APPEARANCE
#========================================================
module_prefix = "appearance"

md = ["# Appearance Utilities"]
md.append(
    r"""## Appearance Guide

The appearance of a segment is defined by a dictionary of the following format:

~~~json
{
    "base_color": "#000000",
    "parallelstripe": ["#000000", "#000000"],
    "perpstripe": ["#000000", "#000000"],
    "twisted": null
}
~~~

### Arguments

**Required**
- `base_color`: exactly one value

**Optional**
- `parallelstripe`: 0+ values (list)
- `perpstripe`: 0+ values (list)
- `twisted`: 0–1 value (`null`, `"RH"`, or `"LH"`)
- `outline_color`: 0–1 value
"""
)
md.append(docs_compiler.commands_header(module_prefix))
md.append(docs_compiler.print_function_docs(appearance.parse, module_prefix))


path = docs_compiler.harnice_dir() / "docs" / "commands" / "appearance.md"
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text("".join(md), encoding="utf-8")