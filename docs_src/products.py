import docs_compiler
#========================================================
# CABLES
#========================================================

md = ["""
# Cables

A "cable" is a COTS or custom physical item that can be mapped onto circuits within a harness part number. 

Something you can purchase by the spool or lot, contains conductor(s) that can be assigned to circuits inside a harness. Usually shows up in a bill of materials. 

"""
]

path = docs_compiler.harnice_dir() / "docs" / "products" / "cable.md"
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text("".join(md), encoding="utf-8")


#========================================================
# CHANNEL TYPES
#========================================================

md = ["""
# Channel Types
Uniquely identifiable set of signals that allow electrical intent to be documented and later referenced

# How to Define New Channel Types

1. In a repository of your choice (or start with [harnice_library_public](https://github.com/harnice/harnice-library-public) on your own branch), navigate to `library_repo/channel_types/channel_types.csv`

1. If you want channel definitions to be private and are therefore working in a private repository, ensure the repo's path is listed in file `library_locations.csv` (located at root of your harnice source code repo). The first column is the URL or traceable path, and the second column is your local path.

1. If you find the channel_type you're looking for, temporarily note it as a touple in a notepad somewhere with format `(ch_type_id, universal_library_repository)`. 

1. If you don't find it, make a new one. It's important to try and reduce the number of channel_types in here to reduce complexity, but it's also important that you adhere to strict and true rules about what is allowed to be mapped to what. Modifications and additions to this document should be taken and reviewed very seriously.
"""
]

path = docs_compiler.harnice_dir() / "docs" / "products" / "channel_type.md"
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text("".join(md), encoding="utf-8")


#========================================================
# DEVICES
#========================================================

md = ["""
# Devices

Harnice defines a device to be **any electrical item that is not a harness.** Devices are the “block” elements in a block diagram, while harnesses are the nets.

Devices contain signals which are part of channels and are mapped to connector cavities. 

The primary data structure of a device is a TSV called a “signals_list”. Signals lists can be written manually or generated from a python script that can help automate the generation of lists for complicated devices.

---
##Rendering a Device

When a Device is rendered in Harnice, here's what happens:

1. Harnice runs the feature tree if it's found in the device directory.
1. The signals list is validated and verified.
1. A KiCad symbol that can be used represent this device in a block diagram is generated or updated based on the signals list.

---
## Device Modeling for Simulation of Behavior in a System (future work)

It is often useful to model how an entire electrical system will behave by aggregating up behaviors of many contained devices and how they interact with each other.

Eventually, Harnice will allow you to do this automatically within the same source-of-truth system definition that defines your harnesses.

When this feature is implemented, devices will contain an automatically generated .kicad_esch file that will allow the user to define a schematic that represents the lump behavior of your device. Harnice will ensure that every signal on your signals list is accounted for in the simulation esch, and the user may choose to connect any simulation device between those symbols. This way, when the device is used in a system block diagram, this device esch can referenced by the system simulator and its behavior can be considered while running an entire system simulation profile.

---

# How Device Definitions are Stored

The definition of a device lives in a CSV file called a "Signals List".

??? info "Signals List"

    {% include-markdown "interacting_with_data/signals_lists.md" %}

---

# How to define a new device
1. Ensure every channel going into or out of a device has a type defined in a repo somewhere.

    ??? info "Channel Types"
        {% include-markdown "products/channel_type.md" %}

1. Make a folder for the part number of your device somewhere on your computer. Run Harnice Render, which will generate an example device that you can then edit.

    ??? info "Rendering a Product"
        {% include-markdown "fragments/how-to-render.md" %}

    You can also lightweight render if you want to bypass some of the checks.

    ??? info "Lightweight Rendering a Product"
        {% include-markdown "fragments/lightweight_rendering.md" %}

1. Edit the attributes of your new device.

    ??? info "Editing the Attributes of a Product"
        {% include-markdown "fragments/editing_attributes.md" %}

1. Edit the signals list of your new device. 

    ??? info "Updating a Signals List"
        {% include-markdown "fragments/how-to-update-signals-list.md" %}

1. Work on your KiCad symbol. 

    ??? info "Working on a Generated Kicad Symbol"
        {% include-markdown "fragments/working-with-a-generated-kicad-symbol.md" %}

"""
]

path = docs_compiler.harnice_dir() / "docs" / "products" / "device.md"
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text("".join(md), encoding="utf-8")

#========================================================
# DISCONNECTS
#========================================================

md = ["""# Disconnect

Set of two electrical connectors that has a predefined pinout, connector selection, and 

In Harnice, any time you need to add connectors in between harnesses, you're required to define the disconnect as a unique part number. Fundamentally, a disconnect part number defines the connector part numbers involved on both sides of the disconnect, the signals running on each of the contacts of the connectors, and which channels those signals are part of. You can reuse a disconnect part number across many systems, which helps to ensure cross-compatibility. When channel mapping a system, Harnice will validate if there are enough available channels through a disconnect to support the device-channel-to-device-channel mapping you're trying to achieve. You can be as specific or as vague as you need about the part numbers and naming (you can always overwrite with logic later) but you must be extremely precise about the electrical information.set of channels that can host circuits.


# How to Make a New Disconnect in Harnice

1. Ensure every channel going into or out of your disconnect has a type defined in a repo somewhere. Each connector of your disconnect will contain information about which side has which direction ("a" contains "inputs", "b" contains "outputs" with respect to the disconnect itself, i.e. inputting into the disconnect)

    ??? info "Channel Types"
        {% include-markdown "products/channel_type.md" %}

1. Make a folder for the part number of your disconnect somewhere on your computer. Run Harnice Render, which will generate an example disconnect that you can then edit.

    ??? info "Rendering a Product"
        {% include-markdown "fragments/how-to-render.md" %}

    You can also lightweight render if you want to bypass some of the checks.

    ??? info "Lightweight Rendering a Product"
        {% include-markdown "fragments/lightweight_rendering.md" %}

1. Edit the attributes of your new disconnect.

    {% include-markdown "fragments/editing_attributes.md" %}

1. Edit the signals list of your new disconnect. 

    ??? info "Updating a Signals List"
        {% include-markdown "fragments/how-to-update-signals-list.md" %}

"""
]
path = docs_compiler.harnice_dir() / "docs" / "products" / "disconnect.md"
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text("".join(md), encoding="utf-8")

#========================================================
# FLAGNOTES
#========================================================

md = ["""
# Flagnote

A bubble shape on a drawing that usually points to something via a leader arrow.
"""
]

path = docs_compiler.harnice_dir() / "docs" / "products" / "flagnote.md"
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text("".join(md), encoding="utf-8")

#========================================================
# HARNESSES
#========================================================

md = ["""# Harness

A set of circuits that satisfies a channel map. Also contains instructions about how to be built from a set of selected parts. 

# How to make a new harness

# What happens when you render?

# Harness Data Structures
Harness data is stored in the following file formats.

??? info "Instances List"

    {% include-markdown "interacting_with_data/instances_lists.md" %}

??? info "Formboard Graph Definition"

    {% include-markdown "interacting_with_data/formboard_graphs.md" %}

??? info "Library Import History"

    {% include-markdown "interacting_with_data/library_history.md" %}

# Examples
"""
]

path = docs_compiler.harnice_dir() / "docs" / "products" / "harness.md"
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text("".join(md), encoding="utf-8")

#========================================================
# MACROS
#========================================================

md = [
    "# Macro"
]

path = docs_compiler.harnice_dir() / "docs" / "products" / "macro.md"
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text("".join(md), encoding="utf-8")

#========================================================
# PARTS
#========================================================

md = [
    """
    # Part
Something you can purchase per each or per unit. May have a 1:1 drawing that can be located on a formboard drawing. usually shows up in a bill of materials.
"""
]

path = docs_compiler.harnice_dir() / "docs" / "products" / "part.md"
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text("".join(md), encoding="utf-8")

#========================================================
# SYSTEMS
#========================================================

md = ["""
# System
A collection of devices and harnesses that satisfies a set of functionality requirements for some external purpose. 

When a python file (feature_tree.py) is called, the KiCad netlist is exported, channels are mapped, and a system instances list is generated. 

Each system has its own feature tree, and it acts as the primary collector for your design rules.



# How to Make a New System
In Harnice, a system is a collection of parts that are connected by harnesses. Collectively, the system itself has a part number, similarly to how an assembly has a part number. The electrical system has its own form/fit/function which is unique to that part number. 

1. Make a folder for the part number of your system somewhere on your computer. Run Harnice Render, which will generate an example system that you can then edit.

    ??? info "Rendering a Product"
        {% include-markdown "fragments/how-to-render.md" %}

    !!! note "Note"
        It will probably fail with `FileNotFoundError: Schematic not found. Check your kicad sch exists at this name and location:`. This is included with the default system feature tree. 

1. Make a new Kicad project located at the path from the above error. Make a schematic in the same directory.

1. Add Harnice devices from a validated device repo as symbols in your kicad_sch. Save and harnice-render it often.

# Designing your Block Diagram in Kicad

Device symbols can be added to your KiCad schematic.

KiCad wires can be drawn that represent entire harnesses.

KiCad is agnostic to the individual conductors, channels, or signals of a harness, just that there are certain connectors that are connected to each other.  


# Adding Harness Disconnects

Add an official Harnice disconnect part to your project and route nets to it. Add the following info to the properties of the disconnect symbol:
    1. in `MPN` write the part number of the disconnect convention
    2. in `lib_repo` write the traceable path to the repo that contains the disconnect convention part number
    3. in `lib_subpath` add the path in between the item_type and the part number, if it exists, for your disconnect, in your library. for example, if your part number is at `{fileio.get_path_to_project(traceable_key)}/disconnect/audio/tascam-db25/tascam-db25-rev1/`, choose `audio/`
    4. in `rev` add the rev you want to use in this system. Optionally, leave it blank.

# What happens when you render?

# System Data Structures
System data is stored in the following file formats.

??? info "Instances List"

    {% include-markdown "interacting_with_data/instances_lists.md" %}

??? info "Library Import History"

    {% include-markdown "interacting_with_data/library_history.md" %}

??? info "Channel Map"

    {% include-markdown "interacting_with_data/channel_maps.md" %}

??? info "Circuits List"

    {% include-markdown "interacting_with_data/circuits_lists.md" %}

??? info "Disconnect Map"

    {% include-markdown "interacting_with_data/disconnect_maps.md" %}

??? info "Netlist"

    {% include-markdown "interacting_with_data/netlists.md" %}

??? info "Post-Harness Instances List"

    {% include-markdown "interacting_with_data/post_harness_instances_lists.md" %}

??? info "Signals List"

    {% include-markdown "interacting_with_data/signals_lists.md" %}

??? info "Manifests"

    {% include-markdown "interacting_with_data/system_manifests.md" %}
    """
]

path = docs_compiler.harnice_dir() / "docs" / "products" / "system.md"
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text("".join(md), encoding="utf-8")


#========================================================
# TITLEBLOCKS
#========================================================

md = ["""
# Titleblock

A page SVG, usually with your name or company logo, that makes your drawings look professional. 
"""
]

path = docs_compiler.harnice_dir() / "docs" / "products" / "titleblock.md"
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text("".join(md), encoding="utf-8")
