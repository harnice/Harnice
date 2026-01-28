*Harnice defines a signals list to be a table that keeps track of every single signal going into and out of a device, which connector or channel it's part of, which signal names it has, which connector contact number or part number it has.*

1. If your device is very simple (has only a small number of signals), you are free to edit `*-signals_list.tsv` manually. If you choose to do this, delete `*-feature_tree.py` before rerunning because by default, it will overwrite the signals list. However, it is recommended that you edit the python feature tree instead to produce a validated, reproduceable, and portable result.
2. To edit the feature tree python file, this quick-start guide should give you an idea of how the default feature tree is set up, and how you might be able to change it to suit your needs. The goal of this feature tree is to make a signals list. Do not be concerned with writing this efficiently, as it will only be ran while rendering the device.
    1. These are useful modules you'll want to reference. Leave them there.
`from harnice.lists import signals_list`
`from harnice.products import chtype`
    1. Copy your channel_type touples in from earlier notepad step. Again, these are relevant only to the device you're trying to make. The dictionary is used to store these here so that you can reference the touples in a human-readable format in this script only.
`ch_type_ids = {`
`    "in": (1, "https://github.com/harnice/harnice"),`
`    "out": (4, "https://github.com/harnice/harnice"),`
`    "chassis": (5, "https://github.com/harnice/harnice")`
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