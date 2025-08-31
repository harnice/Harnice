# Harnice
Harnice is an electrical system design software intended to serve as the glue that holds your electrical system definitions together. Harnice takes software you have used before (KiCad, Altium, Inkscape, Excel, Python, and Github) and support the transaction of information between them.

There are two important functions that Harnice is currently prepared to handle: "Systems" and "Harnesses". A "system" is a collection of "devices" that are connected by "harnesses", where "devices" are any physical device that has connectors on it, and a "harness" is a collection of cables, conductors, connectors, etc, that are used to connect those device connectors together.

# Electrical systems
Systems are defined using PCB schematic software like KiCad or Altium, where a KiCad-component represents a device, and KiCad-nets represents a harness. If you lay out your system definition in this way, you can export a netlist, which represents every connector on every device that is part of the same harness.

The netlist is then traversed and a Channel Map is generated. The Channel Map assigns signals on one connector to other signals on other connectors. Harnice will then validate the channel map. If the channel map fails validation, you'll be prompted with a message like "you're trying to connect signals that are not contained within the same harness" or "you're trying to connect a signal to itself" or "there are unconnected signals in your channel map" or "the channel map disobeys a rule".

Once your channel map is defined and validated, between that and a complete ICD of each device in your system, there should be enough information available to completely define every single harness in your enitre system. To define harnesses, Harnice uses a default set of rules that are easily user-modifiable that generates "instances" on a "system instances list" per harness refdes. There's one system-instances-list per system, and it keeps track of every possible thing in your system like physical parts, build notes, conductors, connections, etc. The system-instances-list that is generated when rendering a system includes all the necessary basic build information about all the harnesses in the system. 

# Harnesses
Harnesses are weird things to model, and here's some of the reasons why: they are infinitely configurable, there's not really a need for perfect 3D cad representation beyond length and space reservation, most of the time they're built by hand, they rely heavily on build notes and procedures to capture design intent. For this reason, when developing Harnice, it was decided that the best way to represent a harness (its software virtual twin, not unlike how a STEP file is the virtual twin to its physically machined counterpart), is an instances list. For this reason, the Harnice software relies heavily on this "harness instances list" for its operation. "Harness instances lists" entirely define everything about one part, and just like "system instances lists", they contain all types of things in your harness, and many attributes about them, but only that apply to this one harness.

When rendering a harness, there are three major steps: prebuilders, build rules, and artifact builders. 

Prebuilders are like converters that take information from other types of files and convert them into harnice instances list format. You could use the Wireviz prebuilder which reads Wireviz-formatted YAML files, or the Harnice Standard Prebuilder, which is similar to Wireviz YAML but is structured differently, or the Harnice System Prebuilder, which scans a "system instances list" for instances only related to the current harness. If you're coming from a different software or have a need to render harnesses formatted in a specific way, you can easily write your own prebuilder in Python.

Once the prebuilders have successfully ran, the user can implement build rules that add or modify instances in the instances list. These are intended to quickly scan the entire instances list for trends or situations in which you want a particular thing done in a specific way for example "if an instance has item_type == connector, add a label to the BOM, and add another instance that represents that label being placed around the associated cable leading to that connector". You can write your own build rules in the form of functions that you can reuse at will. 

Once the build rules have been completed, artifact builders are run. Those are functions that generate the formboard drawings, export XLS bills of materials, wirelist, tooling lists, etc. There is also a PDF artifact builder that makes printable drawings from each harness. Again, if you need some unsupported artifact out of your harness file, you can easily write your own in Python.

Theoretically, this architecture is infinitely scalable, configurable, and customizable, and one thing is for sure, YOU should be using Harnice to record your electrical system information and make your harness drawings!

# Install instructions
# Commands
# Examples
