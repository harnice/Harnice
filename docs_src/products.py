import docs_compiler
from harnice.products import cable, device, disconnect, flagnote, harness, macro, part, system, tblock
# ========================================================
# CABLES
# ========================================================

md = [
    "# Cables\nCOTS or custom physical item, purchased by length, that contains electrical conductors, and are physically installed inside harnesses."
]

path = docs_compiler.harnice_dir() / "docs" / "products" / "_cable.md"
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text("".join(md), encoding="utf-8")


# ========================================================
# CHANNEL TYPES
# ========================================================

md = [
    "# Channel Types\nUniquely identifiable set of signals that allow electrical intent to be documented and later referenced."
]

md.append("""\n\n---\n\n## How to define a new channel type
1. In a repository of your choice (or start with [harnice_library_public](https://github.com/harnice/harnice) on your own branch), navigate to `library_repo/channel_types/channel_types.csv`
1. If you want channel definitions to be private and are therefore working in a private repository, ensure the repo's path is listed in file `library_locations.csv` (located at root of your harnice source code repo). The first column is the URL or traceable path, and the second column is your local path.
1. If you find the channel_type you're looking for, temporarily note it as a touple in a notepad somewhere with format `(ch_type_id, universal_library_repository)`. 
1. If you don't find it, make a new one. It's important to try and reduce the number of channel_types in here to reduce complexity, but it's also important that you adhere to strict and true rules about what is allowed to be mapped to what. Modifications and additions to this document should be taken and reviewed very seriously.""")

path = docs_compiler.harnice_dir() / "docs" / "products" / "_channel_type.md"
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text("".join(md), encoding="utf-8")


# ========================================================
# DEVICES
# ========================================================

md = ["# Devices\nAny electrical item, active or passive, that is not a harness."]

md.append("""\n\n---\n\n##  How device data is stored\n
The primary data structure of a device is a TSV called a “signals_list”. Signals lists can be written manually or generated from a python script that can help automate the generation of lists for complicated devices.\n
The definition of a device lives in a CSV file called a "Signals List".\n
??? info "Signals List"\n
    {% include-markdown "interacting_with_data/_signals_lists.md" %}""")

md.append(docs_compiler.file_structure_to_markdown(device)) 

md.append("""\n\n---\n\n## Rendering a device\n
When a Device is rendered in Harnice, here's what happens:\n
1. Harnice runs the feature tree if it's found in the device directory.
1. The signals list is validated and verified.
1. A KiCad symbol that can be used represent this device in a block diagram is generated or updated based on the signals list.""")

md.append("""\n\n---\n\n## How to define a new device
1. Ensure every channel going into or out of a device has a type defined in a repo somewhere.\n
    ??? info "Channel Types"\n
        {% include-markdown "products/_channel_type.md" %}\n
1. Make a folder for the part number of your device somewhere on your computer. Run Harnice Render, which will generate an example device that you can then edit.\n
    ??? info "Rendering a Product"\n
        {% include-markdown "fragments/how-to-render.md" %}\n
    You can also lightweight render if you want to bypass some of the checks.\n
    ??? info "Lightweight Rendering a Product"\n
        {% include-markdown "fragments/lightweight_rendering.md" %}\n
1. Edit the attributes of your new device.\n
    ??? info "Editing the Attributes of a Product"\n
        {% include-markdown "fragments/editing_attributes.md" %}\n
1. Edit the signals list of your new device.\n
    ??? info "Updating a Signals List"\n
        {% include-markdown "fragments/how-to-update-signals-list.md" %}\n
1. Work on your KiCad symbol.\n
    ??? info "Working on a Generated Kicad Symbol"\n
        {% include-markdown "fragments/working-with-a-generated-kicad-symbol.md" %}\n""")

md.append("""\n\n---\n\n##  Device modeling for simulation of behavior in a system (future work)\n
It is often useful to model how an entire electrical system will behave by aggregating up behaviors of many contained devices and how they interact with each other.\n
Eventually, Harnice will allow you to do this automatically within the same source-of-truth system definition that defines your harnesses.\n
When this feature is implemented, devices will contain an automatically generated .kicad_esch file that will allow the user to define a schematic that represents the lump behavior of your device. Harnice will ensure that every signal on your signals list is accounted for in the simulation esch, and the user may choose to connect any simulation device between those symbols. This way, when the device is used in a system block diagram, this device esch can referenced by the system simulator and its behavior can be considered while running an entire system simulation profile.""")

path = docs_compiler.harnice_dir() / "docs" / "products" / "_device.md"
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text("".join(md), encoding="utf-8")

# ========================================================
# DISCONNECTS
# ========================================================

md = [
    "# Disconnects\nSet of two electrical connectors that has a predefined pinout, connector selection, and signals list.\n"
]

md.append("""\n\n---\n\n## How disconnect data is stored\n
The definition of a disconnect lives in a CSV file called a "Signals List".\n
??? info "Signals List"\n
    {% include-markdown "interacting_with_data/_signals_lists.md" %}\n""")

md.append(docs_compiler.file_structure_to_markdown(disconnect)) 

md.append("""\n\n---\n\n## Rendering a disconnect\n
When a disconnect is rendered in Harnice, here's what happens:\n
1. Harnice runs the feature tree if it's found in the device directory.
1. The signals list is validated and verified.""")

md.append("""\n\n---\n\n## How to define a new disconnect\n
1. Ensure every channel going into or out of your disconnect has a type defined in a repo somewhere. Each connector of your disconnect will contain information about which side has which direction ("a" contains "inputs", "b" contains "outputs" with respect to the disconnect itself, i.e. inputting into the disconnect)\n
    ??? info "Channel Types"\n
        {% include-markdown "products/_channel_type.md" %}\n
1. Make a folder for the part number of your disconnect somewhere on your computer. Run Harnice Render, which will generate an example disconnect that you can then edit.\n
    ??? info "Rendering a Product"\n
        {% include-markdown "fragments/how-to-render.md" %}\n
    You can also lightweight render if you want to bypass some of the checks.\n
    ??? info "Lightweight Rendering a Product"\n
        {% include-markdown "fragments/lightweight_rendering.md" %}\n
1. Edit the attributes of your new disconnect.\n
    ??? info "Editing the Attributes of a Product"\n
        {% include-markdown "fragments/editing_attributes.md" %}\n
1. Edit the signals list of your new disconnect.\n
    ??? info "Updating a Signals List"\n
        {% include-markdown "fragments/how-to-update-signals-list.md" %}\n""")

path = docs_compiler.harnice_dir() / "docs" / "products" / "_disconnect.md"
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text("".join(md), encoding="utf-8")

# ========================================================
# FLAGNOTES
# ========================================================

md = [
    "# Flagnotes\nA bubble shape on a drawing that usually points to something via a leader arrow."
]


md.append(docs_compiler.file_structure_to_markdown(flagnote)) 

path = docs_compiler.harnice_dir() / "docs" / "products" / "_flagnote.md"
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text("".join(md), encoding="utf-8")

# ========================================================
# HARNESSES
# ========================================================

md = [
    "# Harnesses\nA physical assembly that contains a set of electrical circuits that satisfies a channel map. Can also contain other parts and instructions about how to be built. \n"
]

md.append("""\n\n---\n\n## How to define a new harness\n
1. Make a folder for the part number of your harness somewhere on your computer. Run Harnice Render, which will generate an example harness that you can then edit.\n
    ??? info "Rendering a Product"\n
        {% include-markdown "fragments/how-to-render.md" %}\n
    You can also lightweight render if you want to bypass some of the checks.\n
    ??? info "Lightweight Rendering a Product"\n
        {% include-markdown "fragments/lightweight_rendering.md" %}\n
1. Edit the attributes of your new harness.\n
    ??? info "Editing the Attributes of a Product"\n
        {% include-markdown "fragments/editing_attributes.md" %}\n
1. Edit the formboard graph of your new harness.\n
    ??? info "Editing the Formboard Graph of a Product"\n
        {% include-markdown "fragments/editing_formboard_graph.md" %}\n""")

md.append(docs_compiler.file_structure_to_markdown(harness)) 

path = docs_compiler.harnice_dir() / "docs" / "products" / "_harness.md"
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text("".join(md), encoding="utf-8")

# ========================================================
# MACROS
# ========================================================

md = ["# Macros"]

md.append("""\n\n---\n\n## New Macros: Start Here\n
You can copy and paste this template into your new macro (or ai tool) to form the structure of your macro.
```python
# import your modules here

# describe your args here. comment them out and do not officially define because they are called via runpy, 
# for example, the caller feature_tree should define the arguments like this:
# feature_tree_utils.run_macro(
#    "standard_harnice_formboard",
#    "harness_artifacts",
#    "https://github.com/harnice/harnice",
#    artifact_id="formboard-overview",
#    scale=scales.get("A"),
#    input_instances=formboard_overview_instances,
# )

# define the artifact_id of this macro (treated the same as part number). should match the filename.
artifact_id = "example_macro"

# =============== PATHS ===================================================================================
# this function does not need to be called in your macro, just by the default functions below.
# add your file structure inside here: keys are filenames, values are human-readable references. keys with contents are folder names.
# you can also add variables to the filenames, like example_variable_tofu. if you don't need to do this, you can delete references to tofu in this guide.
def macro_file_structure(example_variable_tofu=None):
    # define the dictionary of the file structure of this macro
    return {
        f"{artifact_id}-example.txt": "text file",
        "folder": {
            f"{artifact_id}-{example_variable_tofu}.csv": "csv file",
        }
    }


# this runs automatically and is used to assign a default base directory if it is not called by the caller.
if base_directory == None:  # path between cwd and the file structure for this macro
    base_directory = os.path.join("instance_data", "macro", artifact_id)

# call this in your script to get the path to a file in this macro. it references logic from fileio but passes in the structure from this macro. 
def path(target_value, example_variable_tofu=None):
    return fileio.path(
        target_value,
        structure_dict=macro_file_structure(),
        base_directory=base_directory,
        example_variable_tofu=example_variable_tofu,
        #
    )


def dirpath(target_value):
    # target_value = None will return the root of this macro
    return fileio.dirpath(
        target_value,
        structure_dict=macro_file_structure(),
        base_directory=base_directory,
    )

# don't forget to make the directories you've defined above.
os.makedirs(
    dirpath("folder"),
    exist_ok=True,
)

# macro initialization complete. write the rest of the macro logic here. there are no remaining required functions to call.
# ==========================================================================================================
```
""")

md.append("""# Harnice Macros

Macros are less fundamental commands, are revision controlled like parts, and offer a way for the user to call several instances while modifying each one slightly within your project.


A macro is a chunk of Python that has access to your project files or any other Python-capable function

When you call featuretree_utils.run_macro(), it will import the macro from a library and run it in your script

Some macros are designed to be used to build systems, build harnesses, or export contents “artifacts” from a harness instances list


# Build Macros

Intended to add or modify lines on an instances list based on a standard set of rules or instructions
Can read information from the instances list
Can read information from other support files
Examples
featuretree.runmacro(“import_wireviz_yaml”, “public”)
Reads a wireviz YAML (another commonly used harness design format)
featuretree. runmacro(“add_yellow_htshrk_to_plugs”, “kenyonshutt”)
You can write any rule or set of rules you want in Python, save it to your library, and call it from a harness feature tree.
This one, for example, might scour the instances list:
for plug in instances_list:
if item_type==plug:
instances_list.add(heatshrink, to cable near plug)


# Output Macros
Output Macros will scour the Instances List or other artifact outputs and make other things out of it
BOM
Formboard arrangement
PDF drawing sheet
Analysis calcs
Write your own!
""")

md.append(docs_compiler.file_structure_to_markdown(macro)) 

path = docs_compiler.harnice_dir() / "docs" / "products" / "_macro.md"
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text("".join(md), encoding="utf-8")

# ========================================================
# PARTS
# ========================================================

md = ["# Parts\nBuyable or buildable child item that goes into a harness.\n"]

md.append(docs_compiler.file_structure_to_markdown(part)) 

path = docs_compiler.harnice_dir() / "docs" / "products" / "_part.md"
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text("".join(md), encoding="utf-8")

# ========================================================
# SYSTEMS
# ========================================================

md = [
    "# Systems\nA collection of devices and harnesses that satisfies a set of functionality requirements for some external purpose. "
]

md.append("""\n\n---\n\n## How system data is stored\n
System data is stored in the following file formats.\n
??? info "Instances List"\n
    {% include-markdown "interacting_with_data/_instances_lists.md" %}\n
??? info "Library Import History"\n
    {% include-markdown "interacting_with_data/_library_history.md" %}\n
??? info "Channel Map"\n
    {% include-markdown "interacting_with_data/_channel_maps.md" %}\n
??? info "Circuits List"\n
    {% include-markdown "interacting_with_data/_circuits_lists.md" %}\n
??? info "Disconnect Map"\n
    {% include-markdown "interacting_with_data/_disconnect_maps.md" %}\n
??? info "Netlist"\n
    {% include-markdown "interacting_with_data/_netlists.md" %}\n
??? info "Post-Harness Instances List"\n
    {% include-markdown "interacting_with_data/_post_harness_instances_lists.md" %}\n
??? info "Signals List"\n
    {% include-markdown "interacting_with_data/_signals_lists.md" %}\n
??? info "Manifests"\n
    {% include-markdown "interacting_with_data/_system_manifests.md" %}\n""")

md.append("""\n\n---\n\n## Rendering a system\n
1. Harnice runs the feature tree if it's found in the system directory.\n
1. The system is validated and verified.\n
1. A KiCad symbol that can be used represent this system in a block diagram is generated or updated based on the system.\n""")

md.append(docs_compiler.file_structure_to_markdown(system)) 

md.append("""\n\n---\n\n## How to define a new system\n
1. Make a folder for the part number of your system somewhere on your computer. Run Harnice Render, which will generate an example system that you can then edit.\n
    ??? info "Rendering a Product"\n
        {% include-markdown "fragments/how-to-render.md" %}\n
    !!! note "Note"\n
        It will probably fail with `FileNotFoundError: Schematic not found. Check your kicad sch exists at this name and location:`. This is included with the default system feature tree. \n
1. Make a new Kicad project located at the path from the above error. Make a schematic in the same directory.\n
1. Add Harnice devices from a validated device repo as symbols in your kicad_sch. Save and harnice-render it often.\n""")


md.append("""\n\n---\n\n## Designing your block diagram in Kicad\n
Device symbols can be added to your KiCad schematic.\n
KiCad wires can be drawn that represent entire harnesses.\n
KiCad is agnostic to the individual conductors, channels, or signals of a harness, just that there are certain connectors that are connected to each other via a harness.\n
To add disconnects in between harnesses in your system, add an official Harnice disconnect part to your project and route nets to it. Add the following info to the properties of the disconnect symbol:\n
1. in `MPN` write the part number of the disconnect convention\n
2. in `lib_repo` write the traceable path to the repo that contains the disconnect convention part number\n
3. in `lib_subpath` add the path in between the item_type and the part number, if it exists, for your disconnect, in your library. for example, if your part number is at `{fileio.get_path_to_project(traceable_key)}/disconnect/audio/tascam-db25/tascam-db25-rev1/`, choose `audio/`\n
4. in `rev` add the rev you want to use in this system. Optionally, leave it blank.\n""")

path = docs_compiler.harnice_dir() / "docs" / "products" / "_system.md"
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text("".join(md), encoding="utf-8")


# ========================================================
# TITLEBLOCKS
# ========================================================

md = [
    "# Titleblocks\nA page SVG, usually with your name or company logo, that makes your drawings look professional."
]

md.append(docs_compiler.file_structure_to_markdown(tblock)) 

path = docs_compiler.harnice_dir() / "docs" / "products" / "_titleblock.md"
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text("".join(md), encoding="utf-8")
