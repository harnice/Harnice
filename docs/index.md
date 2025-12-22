# Define "Electrical System"

An electrical system is any collection of circuit boards, electrical boxes, devices, etc, that connect to and interact with each other with wires or harnesses

Examples:

 - Concert sound system
 - Control compute system for plane, car, rocket
 - Commercial power distribution system
 - iPhone
 - City power distribution network

# What Problem is Harnice Trying to Solve?

 - There should always be one single source of truth that describes the devices in your system and how they are connected. Harnice helps designers keep track of it. 
 - Harnice provides a landing pad for designers to be able to define design rules that can build, validate, simulate, or perform any other action on their system design in a clear, concise, human-readable, and machine-readable format.
 - Harnice helps designers produce any possible downstream data that can be derived from the system definition. Any system artifact will always be directly traceable back to the original source of truth. 


## Where does the Harnice Scope End?

 - We’re not yet concerned about what’s going on inside your devices
    - only how they interact with the outside world
    - Software configuration
    - Sure, you can write any rule you want into your Harnice system processor, but Harnice is intended to track hardware.
 - How your electrical hardware interacts with non-electrical things
    - Don’t care about size, weight, fluid type, mounting, physical, thermal, environmental compliance, etc. 
 - As-built configurations
    - Not yet offering ERP/MES functionality

# State of the Art
 - Existing software:
    - Zuken, E-plan, Altium Harnessing, etc
    - SUPER expensive
    - Training-intensive
    - Not user-friendly
    - Not customizable
 - Existing manual options:
    - Literal paper and pen hand drawings
    - Vizio, Powerpoint, Excel, MS Paint, WireViz make good-looking drawings but without metadata
    - Design rule checks impossible
    - Conflicting sources of truth

Instead, let the machines work for you!
Without Harnice…
Designers compile, read, sort through information either from a design guide, from industry knowledge, or other sources…
…manually…
while documenting the results of their studies, until their design is complete. 
Bad because there’s inherently less traceability back to design intent, rampant broken links to sources of truth, results scale proportionally to design time

Instead, with Harnice…
Designers are encouraged to spend their time documenting their design inputs (standards, rules, trades, processes), in a machine-readable format.
So much better because python does the boring work while the designers put their brains to use!

Minimum viable inputs…
Harnice will operate on just the following…
Devices are fully defined
Every signal, channel, connector is accounted for in every device
Sufficient device electrical behavior is defined
A block diagram is drawn by the designer
Each device is accounted for, and each harness connection is made linking connectors
Your rules are qualitatively expressed
Channel mapping preferences
Part selection tree
Length, size, count, device attribute requirements
Any other rule you could possibly ever need
Physical harness routing information can be imported or manually defined

… regard unlimited outputs
Given a system definition, the following can be produced automatically, predictably, effortlessly:
Bill of materials of your entire system 
(devices, harnesses, parts, cable lengths, bits of heat shrink, volume of solder, you name it)
Versions, release dependencies, part number per reference designator, etc
Every harness build drawing, formboard, wirelist in PDF and CSV formats, all at once
Even stylistic choices can be automated into your system render
Electrical behavior
Steady-state and even transient system responses can be simulated with just simple device and harness lump-element definitions
Write your own!
Harnice makes it easy to write simple Python scripts that can tell you anything about your system.


# The Approach
Harnice is a python package that processes netlists and turns them into outputs.
Specify your system definition using Kicad or Altium to make a block diagram
Components represent devices
Nets represent harnesses
Harnice runs a bunch of code on your netlist to determine harness requirements
Builds a channel map
Builds a System Instances List (list of every part and every connection for every harness)
Harnice harness editor can look for a harness inside a system
Adds parts based on standard build rules
Exports build drawings and other artifacts instantaneously

# Harnice’s strict requirement on flexibility
Major departure from existing eCAD packages:
YOU CAN PUT ANYTHING* ANYWHERE.

As long as a thing can be defined as an “instance”, it can end up in your electrical system. Harnice doesn’t care if you need string, nails, plumbing fittings, raccoons, cables, or connectors.

You write your own instance definitions, your own item_types, your own vocabulary, your own relationships.

*The following slides define the exceptions to the above. We couldn’t get away with everything.
