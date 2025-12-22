!!! warning "Notice"
    the first time you render after updating your signals list, you'll probably get an error like `The following pin(s) exist in KiCad symbol but not Signals List: in1, in2, out1, out2`. This is because Harnice is trying to keep your Kicad library symbol up-to-date with your signals list. Simply delete the kicad_sym file if this happens. It will automatically regenerate with the correct pins.
!!! tip "Tip"
    Before you open Kicad, be reasonably sure you've named all of your connectors and they have names you're happy with, and render one more time. This is a convenience measure to ensure the pins that automatically appear in the Kicad file are in sync with your signals list.

1. Open Kicad, add the newly generated library to your library paths (preferences > manage symbol libraries). The command line should have printed lines `Kicad nickname:` and `Kicad path` that you can use when adding the library to your Kicad Library Manager. The provided nickname should already be sufficiently unique and human readable. Refer to Kicad documentation for more support.
1. Open the symbol in Kicad and make the symbol appear the way you want it to look. Do not modify the pin names, but you can change their placement and appearance.
1. When you are done modifying the kicad_sym file, save it, and rerender the harnice part one more time to ensure no mistakes were made.