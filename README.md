# Harnice
Harnice is a free harness design software.

# Versions
Main branch will always track the latest release. 
## V2
- V2 will take the following items from a project folder and produce YAMLs:
  - Kicad netlist
    - export of nexts connecting different connectors of components to each other
    - each net represents a unique harness part number
  - harness manifest
    - list of harness part numbers and their filepaths
    - each line corresponds to new net of netlist
  - connection list
    - list of all existing and designed mating connectors
    - allows user to filter and sort by component, connector name, connector part number, add attributes to each connector, etc
  - channel map
    - list of all available channels
    - where they connect to and from
    - unsolvable or unconnected channels
  - channel map rules
    - instructions on how to auto-generate a channel map
  - project defaults file
    - list of all overrides of part selection defaults
- V2 will also be able to generate a kicad component from a component ICD.
## V1
V1 will take a YAML harness definition and produce a formboard drawing.
## V0
All work happens on V0 until V0 is merged to main to form V1.0.
