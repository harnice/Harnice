# Device
Item you can buy that has signals, connectors, channels. Exhibits electrical behavior. The fundamental “block” element in a block diagram.

Primary data structure of a device is a TSV called “signals_list”.
Generated from a python script that you define
Produces a KiCad symbol that you can import into your project for a block diagram.

Future work: will contain a .kicad_esch file that will allow you to define device electrical behavior.



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

    {% include-markdown "fragments/editing_attributes.md" %}

1. Edit the signals list of your new device. 

    ??? info "Updating a Signals List"
        {% include-markdown "fragments/how-to-update-signals-list.md" %}

1. Work on your KiCad symbol. 

    ??? info "Working on a Generated Kicad Symbol"
        {% include-markdown "fragments/working-with-a-generated-kicad-symbol.md" %}

# Device Configurations

{% include-markdown "fragments/configurations.md" %}

# What happens when you render?

# Device Data Structures

{% include-markdown "fragments/data_structures.md" %}

??? info "Signals List"

    {% include-markdown "interacting_with_data/signals_lists.md" %}

# Examples