# Interacting with Signals Lists
A Signals List is an exhaustive list of every signal is going into or out of a thing. Signals Lists are the primary way Harnice stores information about devices, and act as the source of truth for devices and disconnects.

---
## Signals List Validation Checks:
*(These are automatically validated when you render the device or disconnect that owns the list.)*

{% include-markdown "fragments/signals_list_requirements.md" %}
---
##Columns 
*Columns are automatically generated when `signals_list.new()` is called. Additional columns are not supported and may result in an error when parsing.*
### Columns of Signals Lists for Devices 
=== "`channel_id`"

    Unique identifier for the channel.

=== "`signal`"

    Name of the electrical function of that signal, as it pertains to its channel type defition. i.e. "positive"

=== "`connector_name`"

    Unique identifier for the connector that this signal and channel is a part of.

=== "`cavity`"

    Identifier of the pin, socket, stud, etc, that this signal is internally electrically routed to within its connector.

=== "`connector_mpn`"

    MPN of the connector in this device (NOT the mating connector).

=== "`channel_type`"

    The channel type of this signal. 
    {% include-markdown "fragments/channel_type_reference.md" %}

### Columns of Signals Lists for Disconnects 
=== "`channel_id`"

    Unique identifier for the channel.

=== "`signal`"

    Name of the electrical function of that signal, as it pertains to its channel type defition. i.e. "positive"

=== "`A_cavity`"

    Identifier of the pin, socket, stud, etc, that this signal is internally electrically routed to within that side of the connector.
    ??? question "Why are A and B different here?"
        Sometimes it's possible to have connectors that have cavities that may mate electrically, but have different names. For example, suppose two connectors physically mate, but are made by different manufacturers. One manufacturer used lowercase (a, b, c) to reference the cavities but the other used uppercase (A, B, C), or numbers (1, 2, 3), or colors (red, green, blue), etc.

=== "`B_cavity`"

    Identifier of the pin, socket, stud, etc, that this signal is internally electrically routed to within that side of the connector.
    ??? question "Why are A and B different here?"
        Sometimes it's possible to have connectors that have cavities that may mate electrically, but have different names. For example, suppose two connectors physically mate, but are made by different manufacturers. One manufacturer used lowercase (a, b, c) to reference the cavities but the other used uppercase (A, B, C), or numbers (1, 2, 3), or colors (red, green, blue), etc.

=== "`A_connector_mpn`"

    MPN of the connector of the harness on this side of the disconnect

=== "`A_channel_type`"

    The channel type of this side of the discconect.
    ??? question "Why are A and B different here?"
        It's important to keep track of which side has which channel type so that you cannot accidentally flip pins and sockets, for example, by mapping the wrong channel type to the wrong pin gender. Careful validation should be done when mapping channels through disconnects to ensure the disconnects have channels that pass through them in the correct direction.

=== "`B_connector_mpn`"

    MPN of the connector of the harness on this side of the disconnect

=== "`B_channel_type`"

    The channel type of this side of the discconect.
    ??? question "Why are A and B different here?"
        It's important to keep track of which side has which channel type so that you cannot accidentally flip pins and sockets, for example, by mapping the wrong channel type to the wrong pin gender. Careful validation should be done when mapping channels through disconnects to ensure the disconnects have channels that pass through them in the correct direction.



---

---
##Commands:
*Use the following functions by first importing the module in your script like this: 
```python
from harnice.lists import signals_list
```
 then use as written.*
??? info "`signals_list.set_list_type(x)`"

    Documentation needed.

??? info "`signals_list.new()`"

    Creates a new signals TSV file at fileio.path("signals list") with only the header row.
    Overwrites any existing file.

??? info "`signals_list.append(**kwargs)`"

    Appends a new row to the signals TSV file.
    Missing optional fields will be written as empty strings.
    Raises ValueError if required fields are missing.
    
    Required kwargs:
        For 'device':
            channel_id, signal, connector_name, cavity, connector_mpn, channel_type
        For 'disconnect':
            A_channel_id, A_signal, A_connector_name, A_cavity, A_connector_mpn, A_channel_type,
            B_channel_id, B_signal, B_connector_name, B_cavity, B_connector_mpn, B_channel_type

??? info "`signals_list.cavity_of_signal(channel_id, signal, path_to_signals_list)`"

    Documentation needed.

??? info "`signals_list.connector_name_of_channel(channel_id, path_to_signals_list)`"

    Documentation needed.

---
