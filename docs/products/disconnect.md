# Disconnect

Set of two electrical connectors that has a predefined pinout, connector selection, and set of channels that can host circuits.


# How to Make a New Disconnect in Harnice
In Harnice, any time you need to add connectors in between harnesses, you're required to define the disconnect as a unique part number. Fundamentally, a disconnect part number defines the connector part numbers involved on both sides of the disconnect, the signals running on each of the contacts of the connectors, and which channels those signals are part of. You can reuse a disconnect part number across many systems, which helps to ensure cross-compatibility. When channel mapping a system, Harnice will validate if there are enough available channels through a disconnect to support the device-channel-to-device-channel mapping you're trying to achieve. You can be as specific or as vague as you need about the part numbers and naming (you can always overwrite with logic later) but you must be extremely precise about the electrical information.

1. Ensure your channel types are defined. *Harnice defines "channel" to mean a physical set of physical electrical signals that must be connected to each other. Channels may map to other channels, which later drives conductor, cavity selection, etc.* Each connector of your disconnect should contain information about which side has which direction ("a" contains "inputs", "b" contains "outputs" with respect to the disconnect itself, i.e. inputting into the disconnect)
   https://github.com/harnice/Harnice/blob/357-update-phantom-channel-libraries/documentation/how-to/define-a-new-channel-type.md
1. Build a skeleton for your device.
    1. Navigate to your device folder (`cd` in command line). You don't need to make a rev folder yet, just make sure your command line is in a folder you want to represent the device you're working on. 
    2. Harnice render it (`harnice -r`). It should walk you through the following steps then render an example:
        1. `No valid Harnice file structure detected in 'your_part_number'. Create new PN here? [y]: ` hit enter
        2. `Enter revision number [1]:` hit enter for rev1 or type "A" or whatever you want your first rev to be called
        3. `What product type are you working on? (harness, system, device, etc.): ` type "device"
        4. `Enter a description of this device [DEVICE, FUNCTION, ATTRIBUTES, etc.]:` self-explanatory
        5. `Enter a description for this revision [INITIAL RELEASE]: ` hit enter, otherwise type the goal of the first revision
https://github.com/harnice/Harnice/blob/357-update-phantom-channel-libraries/documentation/how-to/how-to-update-signals-list.md