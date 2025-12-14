# How to Make a New Device in Harnice

1. Ensure your channel types are defined. *Harnice defines "channel" to mean a physical set of physical electrical signals that must be connected to each other. Channels may map to other channels, which later drives conductor, cavity selection, etc.*
    1. In a repository of your choice (start with [harnice_library_public](https://github.com/harnice/harnice-library-public)), navigate to `library_repo/channel_types/channel_types.csv`
    2. If you want channel definitions to be private and are therefore working in a private repository, ensure the repo's path is listed in file `library_locations.csv` (located at root of your harnice source code repo). The first column is the URL or traceable path, and the second column is your local path.
    3. If you find the channel_type you're looking for, temporarily note it as a touple in a notepad somewhere with format `(ch_type_id, universal_library_repository)`. 
    4. If you don't find it, make a new one. It's important to try and reduce the number of channel_types in here to reduce complexity, but it's also important that you adhere to strict and true rules about what is allowed to be mapped to what. Modifications and additions to this document should be taken and reviewed very seriously.
2. Build a skeleton for your device.
    1. Navigate to your device folder (`cd` in command line). You don't need to make a rev folder yet, just make sure your command line is in a folder you want to represent the device you're working on. 
    2. Harnice render it (`harnice -r`). It should walk you through the following steps then render an example:
        1. `No valid Harnice file structure detected in 'your_part_number'. Create new PN here? [y]: ` hit enter
        2. `Enter revision number [1]:` hit enter for rev1 or type "A" or whatever you want your first rev to be called
        3. `What product type are you working on? (harness, system, device, etc.): ` type "device"
        4. `Enter a description of this device [DEVICE, FUNCTION, ATTRIBUTES, etc.]:` self-explanatory
        5. `Enter a description for this revision [INITIAL RELEASE]: ` hit enter, otherwise type the goal of the first revision
3. Edit the attributes of your new device.
    1. Navigate to the device folder, find the new rev folder you just made, open `*-attributes.json`. Change the default reference designator here, as well as any other attributes you may want to record. In the command line, render it again after you `cd` into the rev folder. 
4. Edit the signals list of your new device. *Harnice defines a signals list to be a table that keeps track of every single signal going into and out of a device, which connector or channel it's part of, which signal names it has, which connector contact number or part number it has.*
    1. If your device is very simple (has only a small number of signals), you are free to edit `*-signals_list.tsv` manually. If you choose to do this, delete `*-feature_tree.py` before rerunning because by default, it will overwrite the signals list. However, it is recommended that you edit the python feature tree instead to produce a validated, reproduceable, and portable result.
    1. To edit the feature tree python file, this quick-start guide should give you an idea of how the default feature tree is set up, and how you might be able to change it to suit your needs. The goal of this feature tree is to make a signals list. Do not be concerned with writing this efficiently, as it will only be ran while rendering the device.
        1. These are useful modules you'll want to reference. Leave them there.
`from harnice.lists import signals_list`
`from harnice.products import chtype`
        1. Copy your channel_type touples in from earlier notepad step. Again, these are relevant only to the device you're trying to make. The dictionary is used to store these here so that you can reference the touples in a human-readable format in this script only.
`ch_type_ids = {`
`    "in": (1, "https://github.com/harnice/harnice-library-public"),`
`    "out": (4, "https://github.com/harnice/harnice-library-public"),`
`    "chassis": (5, "https://github.com/harnice/harnice-library-public")`
`}`
        1. Define your pinouts. Default convention is this dictionary, where if you reference something like `xlr_pinout.pos`, this dictionary should return the cavity name. Reminder: channels do not contain information about pinouts or connectors so this has to be done at each device. If you use the same pinout across multiple devices, you may consider importing that definition from a python library elsewhere.
`xlr_pinout = {`
`    "pos": 2,`
`    "neg": 3,`
`    "chassis": 1`
`}`
        1. Define your connector part numbers. Default convention is this dictionary, where you can resolve the part number by finding the connector name. `mpn_for_connector(connector_name)` will search your definition dictionary for a connector name and return its part number.
`connector_mpns = {`
`    "XLR3F": ["in1", "in2"],`
`    "XLR3M": ["out1", "out2"]`
`}`

        1. `signals_list.new()` will overwrite the existing signals list with a blank one, which will be repopulated while the rest of this script is executed.
        2. Bespoke logic should be written in python for the remainder of this script, making use of patterns and naming conventions of this specific device. Read up on the documentation for the available commands in the `harnice.lists.signals_list` and `harnice.products.chtype` modules (NOT YET WRITTEN AT TIME OF WRITING THIS GUIDE)
        3. I'd recommend you use a python editor on your screen at the same time as a csv editor that automatically refreshes (vscode, easycsveditor on the mac store) so that you can update your python, render the code frequently, and watch the updates in realtime on your csv
1. Work on your KiCad symbol. NOTICE: the first time you render after updating your signals list, you'll probably get an error like `The following pin(s) exist in KiCad symbol but not Signals List: in1, in2, out1, out2`. This is because Harnice is trying to keep your Kicad library symbol up-to-date with your signals list. Simply delete the kicad_sym file if this happens. It will automatically regenerate with the correct pins.
    1. After you are reasonably sure you've named all of your connectors and they have names you're happy with (for convenience alone), render one more time to ensure the pins that automatically appear in the Kicad file are in sync with your signals list.
    2. Open Kicad, add the newly generated library to your library paths (preferences > manage symbol libraries). The command line should have spit out a line `Kicad nickname:` that you can use when adding the library to your kicad application. The provided nickname should already be sufficiently unique and human readable. Refer to Kicad documentation for more support.
    3. Open the symbol in Kicad and make the symbol appear the way you want it to look. Do not modify the pin names, but you can change their placement and appearance.
    4. When you are done modifying the kicad_sym file, save it, and rerender the harnice part one more time to ensure no mistakes were made.