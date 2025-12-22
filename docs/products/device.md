# Device
Item you can buy that has signals, connectors, channels. Exhibits electrical behavior. The fundamental “block” element in a block diagram.


# How to define a new device
1. Ensure every channel going into or out of a device has a type defined in a repo somewhere

    ??? info "Channel Types"
        {% include-markdown "products/channel_type.md" %}

1. Run Harnice Render, which will generate an example device that you can then edit.

    ??? info "Rendering a Product"
        {% include-markdown "fragments/how-to-render.md" %}

1. Edit the attributes of your new device.

    Navigate to the device folder, find the new rev folder you just made, open `*-attributes.json`. Change the default reference designator here, as well as any other attributes you may want to record. In the command line, render it again after you `cd` into the rev folder. 

1. Edit the signals list of your new device. 

    ??? info "Updating a Signals List"
        {% include-markdown "fragments/how-to-update-signals-list.md" %}

1. Work on your KiCad symbol. 

    ??? info "Working on a Generated Kicad Symbol"
        {% include-markdown "fragments/working-with-a-generated-kicad-symbol.md" %}

# Device Configurations

# What happens when you render?

# Device Data Structures

# Examples