# Systems
A collection of devices and harnesses that satisfies a set of functionality requirements for some external purpose. 

---

## How system data is stored

System data is stored in the following file formats.

??? info "Instances List"

    {% include-markdown "interacting_with_data/_instances_lists.md" %}

??? info "Library Import History"

    {% include-markdown "interacting_with_data/_library_history.md" %}

??? info "Channel Map"

    {% include-markdown "interacting_with_data/_channel_maps.md" %}

??? info "Circuits List"

    {% include-markdown "interacting_with_data/_circuits_lists.md" %}

??? info "Disconnect Map"

    {% include-markdown "interacting_with_data/_disconnect_maps.md" %}

??? info "Netlist"

    {% include-markdown "interacting_with_data/_netlists.md" %}

??? info "Post-Harness Instances List"

    {% include-markdown "interacting_with_data/_post_harness_instances_lists.md" %}

??? info "Signals List"

    {% include-markdown "interacting_with_data/_signals_lists.md" %}

??? info "Manifests"

    {% include-markdown "interacting_with_data/_system_manifests.md" %}


---

## Rendering a system

1. Harnice runs the feature tree if it's found in the system directory.

1. The system is validated and verified.

1. A KiCad symbol that can be used represent this system in a block diagram is generated or updated based on the system.


## File Structure

Reference the files in your product by calling `fileio.path("file key")` from your script. They'll automatically use this structure:

```
fileio.dirpath("part_directory")                                    |-- yourpn/
                                                                        |-- yourpn-earlier-revs/
                                                                        |-- revhistory.csv
fileio.dirpath("rev_directory")                                         L-- yourpn-revX/
fileio.path("feature tree")                                                 |-- yourpn-revX-feature_tree.py
fileio.path("instances list")                                               |-- yourpn-revX-instances_list.tsv
fileio.path("library history")                                              |-- yourpn-revX-library_import_history.tsv
fileio.dirpath("instance_data")                                             |-- instance_data/
fileio.dirpath("features_for_relatives")                                    |-- features_for_relatives/
fileio.dirpath("harnesses")                                                 |-- harnesses/
fileio.dirpath("lists")                                                     |-- lists/
fileio.path("bom")                                                          |   |-- yourpn-revX-bom.tsv
fileio.path("circuits list")                                                |   |-- yourpn-revX-circuits_list.tsv
fileio.path("post harness instances list")                                  |   |-- yourpn-revX-post_harness_instances_list.tsv
fileio.path("harness manifest")                                             |   |-- yourpn-revX-harness_manifest.tsv
fileio.path("system connector list")                                        |   |-- yourpn-revX-system_connector_list.tsv
fileio.path("mapped channels set")                                          |   |-- yourpn-revX-mapped_channels_set.tsv
fileio.path("mapped disconnects set")                                       |   |-- yourpn-revX-mapped_disconnect_channels_set.tsv
fileio.path("mapped A-side channels through disconnects set")               |   L-- yourpn-revX-mapped_a_channels_through_disconnects_set.tsv
fileio.dirpath("maps")                                                      L-- maps/
fileio.path("channel map")                                                      |-- yourpn-revX-channel_map.tsv
fileio.path("disconnect map")                                                   L-- yourpn-revX-disconnect_map.tsv
```


---

## How to define a new system

1. Make a folder for the part number of your system somewhere on your computer. Run Harnice Render, which will generate an example system that you can then edit.

    ??? info "Rendering a Product"

        {% include-markdown "fragments/how-to-render.md" %}

    !!! note "Note"

        It will probably fail with `FileNotFoundError: Schematic not found. Check your kicad sch exists at this name and location:`. This is included with the default system feature tree. 

1. Make a new Kicad project located at the path from the above error. Make a schematic in the same directory.

1. Add Harnice devices from a validated device repo as symbols in your kicad_sch. Save and harnice-render it often.


---

## Designing your block diagram in Kicad

Device symbols can be added to your KiCad schematic.

KiCad wires can be drawn that represent entire harnesses.

KiCad is agnostic to the individual conductors, channels, or signals of a harness, just that there are certain connectors that are connected to each other via a harness.

To add disconnects in between harnesses in your system, add an official Harnice disconnect part to your project and route nets to it. Add the following info to the properties of the disconnect symbol:

1. in `MPN` write the part number of the disconnect convention

2. in `lib_repo` write the traceable path to the repo that contains the disconnect convention part number

3. in `lib_subpath` add the path in between the item_type and the part number, if it exists, for your disconnect, in your library. for example, if your part number is at `{fileio.get_path_to_project(traceable_key)}/disconnect/audio/tascam-db25/tascam-db25-rev1/`, choose `audio/`

4. in `rev` add the rev you want to use in this system. Optionally, leave it blank.
