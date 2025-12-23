# Disconnect

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

# Disconnect Configurations

{% include-markdown "fragments/configurations.md" %}