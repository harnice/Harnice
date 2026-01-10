from pathlib import Path

#========================================================
# HOW TO REFERENCE CHANNEL TYPES
#========================================================

md = ["""Touple `(x, y)` where x is the channel id within a library repo and y is the traceable name or url where that channel type library is defined"""]

harnice_dir = Path(__file__).resolve().parents[2]
path = harnice_dir / "docs" / "fragments" / "channel_type_reference.md"
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text("".join(md), encoding="utf-8")

#========================================================
# CONFIGURATIONS
#========================================================

md = ["""Harnice subscribes to the idea that a "part number" uniquely identifies a set of items that share identical form, fit, and function. Electrical behavior of a device, however, may sometimes change without altering the physical build, aka form/fit/function, of a device, meaning different electrical behaviors may not necessarily warrant new part numbers.

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

## Manifestation in a """]

harnice_dir = Path(__file__).resolve().parents[2]
path = harnice_dir / "docs" / "fragments" / "configurations.md"
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text("".join(md), encoding="utf-8")

#========================================================
# EDITING ATTRIBUTES
#========================================================

md = ["""1. Navigate to the device folder, find the new rev folder you just made, open `*-attributes.json`. 
1. Change the default reference designator here, as well as any other attributes you may want to record. 
1. In the command line, render it again after you `cd` into the rev folder. """
]

harnice_dir = Path(__file__).resolve().parents[2]
path = harnice_dir / "docs" / "fragments" / "editing_attributes.md"
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text("".join(md), encoding="utf-8")

#========================================================
# HOW TO RENDER
#========================================================

md = ["""1. Navigate to your device folder (`cd` in command line). You don't need to make a rev folder yet, just make sure your command line is in a folder you want to represent the device you're working on. 

1. Harnice render it (`harnice -r`). It should walk you through the following steps then render an example:

    1. `No valid Harnice file structure detected in 'your_part_number'. Create new PN here? [y]: ` hit enter

    1. `Enter revision number [1]:` hit enter for rev1 or type "A" or whatever you want your first rev to be called
    
    1. `What product type are you working on? (harness, system, device, etc.): ` type "device"
    
    1. `Enter a description of this device [DEVICE, FUNCTION, ATTRIBUTES, etc.]:` self-explanatory
    
    1. `Enter a description for this revision [INITIAL RELEASE]: ` hit enter, otherwise type the goal of the first revision"""
]

harnice_dir = Path(__file__).resolve().parents[2]
path = harnice_dir / "docs" / "fragments" / "how-to-render.md"
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text("".join(md), encoding="utf-8")

#========================================================
# HOW TO UPDATE A SIGNALS LIST
#========================================================

md = ["""*Harnice defines a signals list to be a table that keeps track of every single signal going into and out of a device, which connector or channel it's part of, which signal names it has, which connector contact number or part number it has.*

1. If your device is very simple (has only a small number of signals), you are free to edit `*-signals_list.tsv` manually. If you choose to do this, delete `*-feature_tree.py` before rerunning because by default, it will overwrite the signals list. However, it is recommended that you edit the python feature tree instead to produce a validated, reproduceable, and portable result.
2. To edit the feature tree python file, this quick-start guide should give you an idea of how the default feature tree is set up, and how you might be able to change it to suit your needs. The goal of this feature tree is to make a signals list. Do not be concerned with writing this efficiently, as it will only be ran while rendering the device.
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
        3. I'd recommend you use a python editor on your screen at the same time as a csv editor that automatically refreshes (vscode, easycsveditor on the mac store) so that you can update your python, render the code frequently, and watch the updates in realtime on your csv"""
]

harnice_dir = Path(__file__).resolve().parents[2]
path = harnice_dir / "docs" / "fragments" / "how-to-update-signals-list.md"
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text("".join(md), encoding="utf-8")

#========================================================
# LIGHTWEIGHT RENDERING
#========================================================

md = ["""If you need to build a KiCad block diagram quickly, without specifying channels and signals, you can with --lightweight.

Run harnice -l device or harnice --lightweight device from your device directory.

This will follow the same flowchart as --render, but truncate the validation process.

You will not be able to map channels with --lightweight
"""
]

harnice_dir = Path(__file__).resolve().parents[2]
path = harnice_dir / "docs" / "fragments" / "lightweight_rendering.md"
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text("".join(md), encoding="utf-8")

#========================================================
# WORKING WITH A GENERATED KICAD SYMBOL
#========================================================

md = ["""!!! warning "Notice"
    the first time you render after updating your signals list, you'll probably get an error like `The following pin(s) exist in KiCad symbol but not Signals List: in1, in2, out1, out2`. This is because Harnice is trying to keep your Kicad library symbol up-to-date with your signals list. Simply delete the kicad_sym file if this happens. It will automatically regenerate with the correct pins.
!!! tip "Tip"
    Before you open Kicad, be reasonably sure you've named all of your connectors and they have names you're happy with, and render one more time. This is a convenience measure to ensure the pins that automatically appear in the Kicad file are in sync with your signals list.

1. Open Kicad, add the newly generated library to your library paths (preferences > manage symbol libraries). The command line should have printed lines `Kicad nickname:` and `Kicad path` that you can use when adding the library to your Kicad Library Manager. The provided nickname should already be sufficiently unique and human readable. Refer to Kicad documentation for more support.
1. Open the symbol in Kicad and make the symbol appear the way you want it to look. Do not modify the pin names, but you can change their placement and appearance.
1. When you are done modifying the kicad_sym file, save it, and rerender the harnice part one more time to ensure no mistakes were made.

When you render a device Signals List, it’ll make a KiCad schematic symbol in the parent directory

KiCad Symbol will contain ports that match the set of connectors that you’ve specified in Signals List

Render will not affect placement or graphic design of your symbol, just port count and symbol attributes
"""
]

harnice_dir = Path(__file__).resolve().parents[2]
path = harnice_dir / "docs" / "fragments" / "working-with-a-generated-kicad-symbol.md"
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text("".join(md), encoding="utf-8")