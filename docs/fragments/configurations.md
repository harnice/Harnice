It's common to have something that can be used in different ways without physically altering its physical build, form, fit, or function.

Examples:

 - Variable voltage power supply
 - Microphone input either balanced or unbalanced
 - Digitally configurable oscilloscope input

 Harnice is structured such that a device has signals which are part of channels which have types. However, sometimes it's useful to vary the channel type of a set of signals for above reasons.

## Configuration Requirements

  - **Each possible configuration of a device must define the same number of conductors throughout the device**
    - Changing a configuration must not alter physical build, form, fit, or function, and thus there shall be no conductors that are added or taken away. Sure, maybe some are now N/C.

  - **There can be an unlimited number of configuration variables**
    - Sometimes just one variable is useful: SM58, output balanced vs unbalanced
    - Sometimes there are many variables: suppose you have a mixing console with 32 inputs, and each input can have mic or line level inputs and be in balanced or unbalanced format