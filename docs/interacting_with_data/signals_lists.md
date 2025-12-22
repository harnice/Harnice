# Interacting with Signals Lists

A list of circuits that appear on connectors and are part of channels that belong to a device

Signals Lists are the primary way Harnice stores information about devices
Source of truth for devices or disconnects
Exhaustive list of every electrical connection going into or out of the device or disconnect

# Rules about Signals Lists
Every combination of (channel_id, signal) must be unique within the signals list
You can’t have two “ch1, pos” signals on the same device
Every signal of a channel_type must be present in the Signals List
If your channel_type requires “positive” and “negative”, you have to have both in your signals list
Every signal in the Signals List must be present in the channel_type
If you need to add signals that aren’t already part of your pre-defined channel_type, you’ll need to define a new channel_type.
You can’t put signals of the same channel on different connectors
While this may sound convenient, it breaks a lot of internal assumptions Harnice is making on the back end about how to map channels. 
If you need to do this, I recommend defining one channel type per signal, then write a macro for mapping the channels to their respective destinations.
“A” and “B” channels of the same disconnect must be compatible with each other
