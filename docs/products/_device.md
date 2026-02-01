# Devices
Any electrical item, active or passive, that is not a harness.

---

##  How device data is stored

The primary data structure of a device is a TSV called a “signals_list”. Signals lists can be written manually or generated from a python script that can help automate the generation of lists for complicated devices.

The definition of a device lives in a CSV file called a "Signals List".

??? info "Signals List"

    {% include-markdown "interacting_with_data/_signals_lists.md" %}

## File Structure

Reference the files in your product by calling `fileio.path("file key")` from your script. They'll automatically use this structure:

```
fileio.dirpath("part_directory")       |-- yourpn/
                                           |-- earlier revs/
                                           |-- revhistory.csv
fileio.dirpath("rev_directory")                                            L-- your rev/
fileio.path("feature tree")                    |-- yourpn-revX-feature_tree.py
fileio.path("signals list")                    |-- yourpn-revX-signals_list.tsv
fileio.path("attributes")                      L-- yourpn-revX-attributes.json
```


---

## Rendering a device

When a Device is rendered in Harnice, here's what happens:

1. Harnice runs the feature tree if it's found in the device directory.
1. The signals list is validated and verified.
1. A KiCad symbol that can be used represent this device in a block diagram is generated or updated based on the signals list.

---

## How to define a new device
1. Ensure every channel going into or out of a device has a type defined in a repo somewhere.

    ??? info "Channel Types"

        {% include-markdown "products/_channel_type.md" %}

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


---

##  Device modeling for simulation of behavior in a system (future work)

It is often useful to model how an entire electrical system will behave by aggregating up behaviors of many contained devices and how they interact with each other.

Eventually, Harnice will allow you to do this automatically within the same source-of-truth system definition that defines your harnesses.

When this feature is implemented, devices will contain an automatically generated .kicad_esch file that will allow the user to define a schematic that represents the lump behavior of your device. Harnice will ensure that every signal on your signals list is accounted for in the simulation esch, and the user may choose to connect any simulation device between those symbols. This way, when the device is used in a system block diagram, this device esch can referenced by the system simulator and its behavior can be considered while running an entire system simulation profile.