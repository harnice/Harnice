Harnice subscribes to the idea that a "part number" uniquely identifies a set of items that share identical form, fit, and function. Electrical behavior of a device, however, may sometimes change without altering the physical build, aka form/fit/function, of a device, meaning different electrical behaviors may not necessarily warrant new part numbers.

The way to get around this is to allow part numbers to contain "configurations", which define **how** an item is used, not **what** the item is.

Examples:

 - Power supply with multiple output voltage settings
 - Audio preamplifier that works for both balanced or unbalanced inputs
 - Digitally configurable data acquisition input
 - Antenna used as a transmitter OR a receiver

In the above examples, the same part is used in different ways without physically rebuilding or rewiring itself. 

Harnice treats these as the same device with different configurations. 

To configure a device, all you're doing is changing the signals list. Each signal exists, but depending on the configuration, may be mapped to a different cavity in a connector or a different channel type.

## Configuration Requirements

  - **Each possible configuration of a device must define the same number of conductors throughout the device**
    - Changing a configuration must not alter physical build, form, fit, or function, and thus there shall be no conductors that are added or taken away. Sure, maybe some are now N/C.

  - **There can be an unlimited number of configuration variables**
    - Sometimes just one variable is useful: SM58, output balanced vs unbalanced
    - Sometimes there are many variables: suppose you have a mixing console with 32 inputs, and each input can have mic or line level inputs and be in balanced or unbalanced format

## Manifestation in a 