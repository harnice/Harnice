# System
A collection of devices and harnesses that satisfies a set of functionality requirements for some external purpose. 


# How to Make a New System
In Harnice, a system is a collection of parts that are connected by harnesses. Collectively, the system itself has a part number, similarly to how an assembly has a part number. The electrical system has its own form/fit/function which is unique to that part number. 

1. Get the file structure set up
    1. Create and navigate to (`cd` in command line) a folder you want to contain your system. The folder name is the system part number. You don't need to make a rev folder yet.
    2. Harnice render it (`harnice -r`). It should walk you through the following steps then render an example:
        1. `No valid Harnice file structure detected in 'your_part_number'. Create new PN here? [y]: ` hit enter
        2. `Enter revision number [1]:` hit enter for rev1 or type "A" or whatever you want your first rev to be called
        3. `What product type are you working on? (harness, system, device, etc.): ` type "system"
        4. `Enter a description of this device [DEVICE, FUNCTION, ATTRIBUTES, etc.]:` self-explanatory
        5. `Enter a description for this revision [INITIAL RELEASE]: ` hit enter, otherwise type the goal of the first revision
    3. It will probably fail with `FileNotFoundError: Schematic not found. Check your kicad sch exists at this name and location:`. This is included with the default system feature tree. 
    4. Make a new Kicad project located at the path from the above error. Make a schematic in the same directory. Add Harnice devices from a validated device repo as symbols in your kicad_sch. Save it and run `harnice -r`.
    5. At this point, it is not expected that you'll see any setup errors when rendering your system. You might see other ones, but they should be related to the configuration of your specific system.
2. if you need to add a disconnect to one of the harnesses in your system, add it from the harnice library. add the following info to the properties of the disconnect symbol:
    1. in `MPN` write the part number of the disconnect convention
    2. in `lib_repo` write the traceable path to the repo that contains the disconnect convention part number
    3. in `lib_subpath` add the path in between the item_type and the part number, if it exists, for your disconnect, in your library. for example, if your part number is at `{fileio.get_path_to_project(traceable_key)}/disconnect/audio/tascam-db25/tascam-db25-rev1/`, choose `audio/`
    4. in `rev` add the rev you want to use in this system. Optionally, leave it blank.