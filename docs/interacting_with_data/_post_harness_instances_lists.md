# Interacting with Post Harness Instances Lists

    A list of every physical or notional thing, drawing element, or concept that includes instances added at the harness level, that represents a system
    
---
##Commands:
*Use the following functions by first importing the module in your script like this: 
```python
from harnice.lists import library_history
```
 then use as written.*
??? info "`library_history.rebuild()`"

    Build the 'post harness instances list' by merging instance data from:
      - Each harness's instances list if the harness_pn is defined and file exists
      - Otherwise, fall back to the system-level instances list for matching nets
    
    Writes a clean TSV with INSTANCES_LIST_COLUMNS.

??? info "`library_history.push(path_to_system_rev, system_pn_rev)`"

    Documentation needed.

