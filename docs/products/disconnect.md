# Disconnects
Set of two electrical connectors that has a predefined pinout, connector selection, and signals list.


---

## How Disconnect Definitions are Stored

The definition of a disconnect lives in a CSV file called a "Signals List".

??? info "Signals List"

    {% include-markdown "interacting_with_data/signals_lists.md" %}


---

## Rendering a disconnect

When a disconnect is rendered in Harnice, here's what happens:

1. Harnice runs the feature tree if it's found in the device directory.
1. The signals list is validated and verified.

---

## How to define a new disconnect in Harnice

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

    ??? info "Editing the Attributes of a Product"

        {% include-markdown "fragments/editing_attributes.md" %}

1. Edit the signals list of your new disconnect.

    ??? info "Updating a Signals List"

        {% include-markdown "fragments/how-to-update-signals-list.md" %}
