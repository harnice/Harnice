### General Signals List Rules

 - Each signal defined in the list is contained by one or more cavities of connectors. 
     - you can't "cap off" or not populate one of the signals within a channel because that changes the channel type.

 - Every signal in the Signals List must be contained by a pre-defined channel type

    ??? info "Channel Types"
        {% include-markdown "products/channel_type.md" %}

 - Each signal in the signals list must have every other signal defined by its channel type also present in the list.
    - you can't just define 'positive' if the channel type requires 'positive' and 'negative'

 - Every combination of (channel_id, signal) must be unique within the signals list
    - you can’t have two i.e. “ch1, pos” signals on the same device
    - if you need to break one signal out onto multiple conductors, you'll need to change the channel type to one that defines multiple conductors (i.e. named "ch1, pos-1")

 - You can’t put signals of the same channel on different connectors
    - this is because doing so breaks a lot of internal assumptions Harnice is making while mapping channels.

    - the following two options are recommended work-arounds:
    
        - **Most correct but confusing:** Define one channel type per signal, then manually chmap your channels or write a macro for mapping the channels to their respective destinations.

        - **Janky but easiest to understand:** Define a connector part number that actually represents multiple connectors, while using cavities to reference each connector.

### Configurable Device Signals List Rules

  - **Each possible configuration of a device must define the same number of conductors throughout the device**
    - Changing a configuration must not alter physical build, form, fit, or function, and thus there shall be no conductors that are added or taken away. Sure, maybe some are now N/C.

  - **There can be an unlimited number of configuration variables**
    - Sometimes just one variable is useful: SM58, output balanced vs unbalanced
    - Sometimes there are many variables: suppose you have a mixing console with 32 inputs, and each input can have mic or line level inputs and be in balanced or unbalanced format

### Disconnect Signals List Rules

 - “A” and “B” channels of the same disconnect must be compatible with each other

     - this is to ensure when you actually mate the disconnect that the channels inside will be compatible.
