# Appearance Utilities## Appearance Guide

    The appearance of a segment is defined by a dictionary of the following format:

    ~~~json
    {
        "base_color": "#000000",
        "parallelstripe": ["#000000", "#000000"],
        "perpstripe": ["#000000", "#000000"],
        "twisted": null
    }
    ~~~

    ### Arguments

    **Required**
    - `base_color`: exactly one value

    **Optional**
    - `parallelstripe`: 0+ values (list)
    - `perpstripe`: 0+ values (list)
    - `twisted`: 0–1 value (`null`, `"RH"`, or `"LH"`)
    - `outline_color`: 0–1 value
    
---
##Commands:
*Use the following functions by first importing the module in your script like this: 
```python
from harnice.lists import appearance
```
 then use as written.*
??? info "`appearance.parse(val)`"

    Parse appearance dictionary, converting color names and shorthand hex to full hex.
    No validation or safeguards.

