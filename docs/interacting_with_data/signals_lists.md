A **Signals List** is an exhaustive list of every signal is going into or out of a thing. Signals Lists are the primary way Harnice stores information about devices, and act as the source of truth for devices and disconnects.

 - Each signal is contained by one or more cavities of connectors
 - Each signal may be assigned to a functional signal of a channel, or left unused.
---
## Columns
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

## Signals Lists have rules...

 - Every combination of (channel_id, signal) must be unique within the signals list
    - i.e. you can’t have two “ch1, pos” signals on the same device

 - Signals of channels in a signals list must agree with their channel type definitions
    - If a signal is on the list that has a channel name and a channel type, all of the required signals of that channel type must also be present in the list with the same channel name (you can't just define 'positive' if the channel type requires 'positive' and 'negative')

 - Every signal in the Signals List must have a pre-defined channel type

    ??? info "Channel Types"
        {% include-markdown "products/channel_type.md" %}

 - You can’t put signals of the same channel on different connectors
    - While this may sound inconvenient, it breaks a lot of internal assumptions Harnice is making on the back end about how to map channels. 

    - If you need to do this, I recommend the following two options:
    
        - **Most correct but confusing:** Define one channel type per signal, then manually chmap your channels or write a macro for mapping the channels to their respective destinations.

        - **Janky but easiest to understand:** Define a connector part number that actually represents multiple connectors, while using cavities to reference each connector.

 - “A” and “B” channels of the same disconnect must be compatible with each other

---

##Commands:
??? info "`signals_list.set_list_type()`"

    No documentation provided.

??? info "`signals_list.new()`"

    Creates a new signals TSV file at fileio.path("signals list") with only the header row.
    Overwrites any existing file.

??? info "`signals_list.append()`"

    Appends a new row to the signals TSV file.
    Missing optional fields will be written as empty strings.
    Raises ValueError if required fields are missing.
    
    Required kwargs:
        For 'device':
            channel_id, signal, connector_name, cavity, connector_mpn, channel_type
        For 'disconnect':
            A_channel_id, A_signal, A_connector_name, A_cavity, A_connector_mpn, A_channel_type,
            B_channel_id, B_signal, B_connector_name, B_cavity, B_connector_mpn, B_channel_type

??? info "`signals_list.cavity_of_signal()`"

    No documentation provided.

??? info "`signals_list.connector_name_of_channel()`"

    No documentation provided.

---
