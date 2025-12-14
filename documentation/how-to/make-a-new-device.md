# How to Make a New Device in Harnice

1. Ensure your channel types are defined. *Harnice defines "channel" to mean a physical set of physical electrical signals that must be connected to each other. Channels may map to other channels, which later drives conductor, cavity selection, etc.*
   https://github.com/harnice/Harnice/blob/357-update-phantom-channel-libraries/documentation/how-to/define-a-new-channel-type.md
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

1. Work on your KiCad symbol. NOTICE: the first time you render after updating your signals list, you'll probably get an error like `The following pin(s) exist in KiCad symbol but not Signals List: in1, in2, out1, out2`. This is because Harnice is trying to keep your Kicad library symbol up-to-date with your signals list. Simply delete the kicad_sym file if this happens. It will automatically regenerate with the correct pins.
    1. After you are reasonably sure you've named all of your connectors and they have names you're happy with (for convenience alone), render one more time to ensure the pins that automatically appear in the Kicad file are in sync with your signals list.
    2. Open Kicad, add the newly generated library to your library paths (preferences > manage symbol libraries). The command line should have spit out a line `Kicad nickname:` that you can use when adding the library to your kicad application. The provided nickname should already be sufficiently unique and human readable. Refer to Kicad documentation for more support.
    3. Open the symbol in Kicad and make the symbol appear the way you want it to look. Do not modify the pin names, but you can change their placement and appearance.
    4. When you are done modifying the kicad_sym file, save it, and rerender the harnice part one more time to ensure no mistakes were made.