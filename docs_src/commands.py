import docs_functions
from harnice.utils import (
    feature_tree_utils,
    library_utils,
    circuit_utils,
    formboard_utils,
    note_utils,
    svg_utils,
    system_utils,
    appearance,
)
from harnice import fileio, state


def main():
    # ========================================================
    # LIBRARY UTILS
    # ========================================================
    module_prefix = "library_utils"

    md = ["# Library Utilities"]
    md.append(docs_functions.commands_header(module_prefix))
    md.append(docs_functions.print_function_docs(library_utils.pull, module_prefix))
    md.append(
        docs_functions.print_function_docs(library_utils.get_local_path, module_prefix)
    )

    path = docs_functions.harnice_dir() / "docs" / "commands" / "_library_utils.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(md), encoding="utf-8")

    # ========================================================
    # CIRCUIT UTILS
    # ========================================================
    module_prefix = "circuit_utils"

    md = ["# Circuit Utilities"]
    md.append(docs_functions.commands_header(module_prefix))
    md.append(
        docs_functions.print_function_docs(
            circuit_utils.end_ports_of_circuit, module_prefix
        )
    )
    md.append(
        docs_functions.print_function_docs(
            circuit_utils.max_port_number_in_circuit, module_prefix
        )
    )
    md.append(
        docs_functions.print_function_docs(
            circuit_utils.squeeze_instance_between_ports_in_circuit, module_prefix
        )
    )
    md.append(
        docs_functions.print_function_docs(
            circuit_utils.instances_of_circuit, module_prefix
        )
    )
    md.append(
        docs_functions.print_function_docs(
            circuit_utils.instance_of_circuit_port_number, module_prefix
        )
    )
    md.append(
        docs_functions.print_function_docs(
            circuit_utils.circuit_instance_of_instance, module_prefix
        )
    )
    md.append(
        docs_functions.print_function_docs(
            circuit_utils.assign_cable_conductor, module_prefix
        )
    )
    path = docs_functions.harnice_dir() / "docs" / "commands" / "_circuits_utils.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(md), encoding="utf-8")

    # ========================================================
    # FEATURE TREE UTILS
    # ========================================================
    module_prefix = "feature_tree_utils"

    md = ["# Feature Tree Utilities"]
    md.append(docs_functions.commands_header(module_prefix))
    md.append(
        docs_functions.print_function_docs(feature_tree_utils.run_macro, module_prefix)
    )
    md.append(
        docs_functions.print_function_docs(
            feature_tree_utils.lookup_outputcsys_from_lib_used, module_prefix
        )
    )
    md.append(
        docs_functions.print_function_docs(
            feature_tree_utils.copy_pdfs_to_cwd, module_prefix
        )
    )
    md.append(
        docs_functions.print_function_docs(
            feature_tree_utils.run_feature_for_relative, module_prefix
        )
    )

    path = docs_functions.harnice_dir() / "docs" / "commands" / "_feature_tree_utils.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(md), encoding="utf-8")

    # ========================================================
    # FORMBOARD UTILS
    # ========================================================
    module_prefix = "formboard_utils"
    md = ["# Formboard Utilities"]
    md.append(docs_functions.commands_header(module_prefix))
    md.append(
        docs_functions.print_function_docs(
            formboard_utils.validate_nodes, module_prefix
        )
    )
    md.append(
        docs_functions.print_function_docs(
            formboard_utils.map_instance_to_segments, module_prefix
        )
    )
    md.append(
        docs_functions.print_function_docs(
            formboard_utils.calculate_location, module_prefix
        )
    )
    md.append(
        docs_functions.print_function_docs(formboard_utils.draw_line, module_prefix)
    )

    path = docs_functions.harnice_dir() / "docs" / "commands" / "_formboard_utils.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(md), encoding="utf-8")

    # ========================================================
    # NOTE UTILS
    # ========================================================

    module_prefix = "note_utils"
    md = ["# Note Utilities"]
    md.append(docs_functions.commands_header(module_prefix))
    md.append(docs_functions.print_function_docs(note_utils.new_note, module_prefix))
    md.append(
        docs_functions.print_function_docs(
            note_utils.assign_buildnote_numbers, module_prefix
        )
    )
    md.append(
        docs_functions.print_function_docs(
            note_utils.make_rev_history_notes, module_prefix
        )
    )
    md.append(
        docs_functions.print_function_docs(note_utils.make_bom_flagnote, module_prefix)
    )
    md.append(
        docs_functions.print_function_docs(
            note_utils.make_part_name_flagnote, module_prefix
        )
    )
    md.append(
        docs_functions.print_function_docs(
            note_utils.make_buildnote_flagnote, module_prefix
        )
    )
    md.append(
        docs_functions.print_function_docs(
            note_utils.make_rev_change_flagnote, module_prefix
        )
    )
    md.append(
        docs_functions.print_function_docs(
            note_utils.parse_note_instance, module_prefix
        )
    )
    md.append(
        docs_functions.print_function_docs(
            note_utils.get_lib_build_notes, module_prefix
        )
    )
    md.append(
        docs_functions.print_function_docs(note_utils.get_lib_tools, module_prefix)
    )
    md.append(
        docs_functions.print_function_docs(note_utils.combine_notes, module_prefix)
    )

    path = docs_functions.harnice_dir() / "docs" / "commands" / "_note_utils.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(md), encoding="utf-8")

    # ========================================================
    # SVG UTILS
    # ========================================================
    module_prefix = "svg_utils"

    md = ["# SVG Utilities"]
    md.append(docs_functions.commands_header(module_prefix))
    md.append(docs_functions.print_function_docs(svg_utils.table, module_prefix))
    md.append(
        docs_functions.print_function_docs(
            svg_utils.add_entire_svg_file_contents_to_group, module_prefix
        )
    )
    md.append(
        docs_functions.print_function_docs(
            svg_utils.find_and_replace_svg_group, module_prefix
        )
    )
    md.append(
        docs_functions.print_function_docs(svg_utils.draw_styled_path, module_prefix)
    )

    path = docs_functions.harnice_dir() / "docs" / "commands" / "_svg_utils.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(md), encoding="utf-8")

    # ========================================================
    # SYSTEM UTILS
    # ========================================================
    module_prefix = "system_utils"
    md = ["# System Utilities"]
    md.append(docs_functions.commands_header(module_prefix))
    md.append(
        docs_functions.print_function_docs(
            system_utils.mpn_of_device_refdes, module_prefix
        )
    )
    md.append(
        docs_functions.print_function_docs(
            system_utils.connector_of_channel, module_prefix
        )
    )
    md.append(
        docs_functions.print_function_docs(
            system_utils.find_connector_with_no_circuit, module_prefix
        )
    )
    md.append(
        docs_functions.print_function_docs(
            system_utils.make_instances_for_connectors_cavities_nodes_channels_circuits,
            module_prefix,
        )
    )
    md.append(
        docs_functions.print_function_docs(
            system_utils.add_chains_to_channel_map, module_prefix
        )
    )
    md.append(
        docs_functions.print_function_docs(
            system_utils.make_instances_from_bom, module_prefix
        )
    )

    path = docs_functions.harnice_dir() / "docs" / "commands" / "_system_utils.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(md), encoding="utf-8")

    # ========================================================
    # APPEARANCE
    # ========================================================
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
    md.append(docs_functions.commands_header(module_prefix))
    md.append(docs_functions.print_function_docs(appearance.parse, module_prefix))

    path = docs_functions.harnice_dir() / "docs" / "commands" / "_appearance.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(md), encoding="utf-8")

    # ========================================================
    # INTERACTING WITH FILES
    # ========================================================

    md = [
        """# Keeping Track of Files

The `fileio` module keeps files organized! With the tools described in this page, you should never need to reference a file by constructing a path from scratch.

## Part number and revision folders

Harnice requires a revision folder and a part number folder to be able to render any product.

```python
# suppose your part number is "123456" and your revision is "A"

|-- A123456/
    L--   A123456-revA/
```

If you're starting a new product, just make a new part number folder, run `harnice -r` from that folder in the command line, and the command line will help you build the right structure. 

Revision history data will be stored automatically inside the part number folder. That is the file that tells Harnice what kind of product you're currently working on, among other things. 

If you need to make a new revision of a product, navigate to a part or a rev folder in your command line, then enter `harnice --newrev`.

## Product file structures

Products and macros have their own pre-defined **file structure**. It's stored as a function inside the Harnice source code. Here's an example of the **Harness** one:

```python
def file_structure(): # example of a file structure of a product
    return {
        f"{state.partnumber('pn-rev')}-feature_tree.py": "feature tree",
        f"{state.partnumber('pn-rev')}-instances_list.tsv": "instances list",
        f"{state.partnumber('pn-rev')}-formboard_graph_definition.png": "formboard graph definition png",
        f"{state.partnumber('pn-rev')}-library_import_history.tsv": "library history",
        "interactive_files": {
            f"{state.partnumber('pn-rev')}.formboard_graph_definition.tsv": "formboard graph definition",
        },
    }
```

A file structure is defined for each product or macro. It is automatically passed into the code when that product or macro is ran. 

Here's the basics of how to read a file structure dictionary:

- **Files**: each file is a key–value pair where the **key** is the filename and the **value** is a short, human-readable **file key** (e.g. `"myfile.tsv": "signals list"`). You use the file key with `fileio.path("signals list")`.
- **Directories**: a directory is a key whose **value** is another dict (empty `{}` or more key–value pairs). The **key** is the directory name and is what you pass to `fileio.dirpath("dirname")`.

## Quick-start: accessing default files
\n\n"""
    ]

    md.append(docs_functions.print_function_docs(fileio.path, "fileio"))
    md.append(docs_functions.print_function_docs(fileio.dirpath, "fileio"))

    md.append("""

Use these two functions to access fils of any product. For most purposes, you can omit `structure_dict` and `base_directory`.

## The other arguments in `fileio.path()` and `fileio.dirpath()`

You can see from the above two functions that there are two optional arguments: `structure_dict` and `base_directory`. Here's what those mean:

**`structure_dict`:**

 - This is the file structure dictionary that is actually parsed to find the file path.
 - By default, the file structure of the product that's currently being run by Harnice is passed in at runtime.
 - Alternatively, if you need to pass a special structure dict in, you can do that here. You can do this, for example, if you have a custom macro or a custom file structure preference for an existing product.

**`base_directory`:**

 - This is the directory from which the relative paths from the file structure dictionary originates. 
 - By default, this is set to the revision folder of the product you're working on. This means that the file structure dictionary of the product is in reference to, or added on top of, the revision file of the current product.
 - If you need to reference files in another project, for example, or recursively with a macro that's called as an instance, that has its own sub-instances, you can change the base directory of the file structure dictionary to point to wherever you want with this. 

## Parametric file names in your folder structure

You can add extra arguments to `file_structure()` (and pass a custom dict into fileio) for more complex layouts. For example, maybe you need a filename that is controlled by a variable, like in this example:

```python
def macro_file_structure(page_name=None, page_counter=None):
    return {
        f"{state.partnumber('pn-rev')}-{artifact_id}-page_setup.json": "page setup",
        f"{artifact_id}-mastercontents.svg": "master contents svg",
        f"{state.partnumber('pn-rev')}-{artifact_id}.pdf": "output pdf",
        "page_svgs": {
            f"{page_counter}-{page_name}-user-editable.svg": "user editable page svg"
        },
    }
```

## Accessing the current part number and rev

Behind the scenes, Harnice stores the current part number and revision number in the module `state`. You can query it in any format you may need. \n\n""")

    md.append(docs_functions.print_function_docs(state.partnumber, "state"))

    module_prefix = "fileio"
    md.append(docs_functions.commands_header("fileio"))
    md.append(docs_functions.print_function_docs(state.partnumber, "state"))
    md.append(docs_functions.print_function_docs(fileio.path, module_prefix))
    md.append(docs_functions.print_function_docs(fileio.dirpath, module_prefix))
    md.append(docs_functions.print_function_docs(fileio.silentremove, module_prefix))
    md.append(
        docs_functions.print_function_docs(
            fileio.get_git_hash_of_harnice_src, module_prefix
        )
    )
    md.append(
        docs_functions.print_function_docs(fileio.get_path_to_project, module_prefix)
    )
    md.append(docs_functions.print_function_docs(fileio.read_tsv, module_prefix))
    md.append(docs_functions.print_function_docs(fileio.drawnby, module_prefix))
    md.append(
        "This one happens behind the scenes, but here's how it knows you're in the right folder structure:\n\n"
    )
    md.append(
        docs_functions.print_function_docs(
            fileio.verify_revision_structure, module_prefix
        )
    )

    path = docs_functions.harnice_dir() / "docs" / "commands" / "_manipulating_files.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(md), encoding="utf-8")
