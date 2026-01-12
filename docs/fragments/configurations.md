Harnice subscribes to the idea that a "part number" uniquely identifies the design of a component. If you are making changes to a component that has been "released", built, or its design intent has been otherwise established, and you somehow modify the **form, fit, or function** of that part or any of its child components, you therefore must change the part number (drawing revisions, documentation, etc do not count). 

Electrical behavior of a device, however, may sometimes change without altering the physical build, aka **form, fit, or function**, of that device, meaning different electrical behaviors may not necessarily warrant new part numbers.

The way to keep track of this wiithin Harnice is to allow part numbers to contain "configurations", which define **how** an item is used, not **what** the item is.

Examples:

 - Power supply with multiple output voltage settings
 - Audio preamplifier that works for both balanced or unbalanced inputs
 - Digitally configurable analog-to-digital converter input
 - Antenna used as a transmitter OR a receiver

In the above examples, the same part is used in different ways without physically rebuilding or rewiring itself. Therefore, these can be treated within Harnice as the same device with different configurations. 

When you select a configuration of a device, all you're doing is changing which rows of the signals list are currently being read. There now may be multiple rows for the same signal, but only one applies based on the current configuration.