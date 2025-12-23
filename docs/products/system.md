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
{% include-markdown "fragments/data_structures.md" %}

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