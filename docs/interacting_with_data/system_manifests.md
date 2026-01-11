# Interacting with System Manifests
A table that relates reference designator to part number(s), and may contain other information indexed to the reference designator

---
##Columns 
*Columns are automatically generated when `manifest.new()` is called. Additional columns are not supported and may result in an error when parsing.*
=== "`net`"

    documentation needed

=== "`harness_pn`"

    documentation needed


---
##Commands:
*Use the following functions by first importing the module in your script like this: 
```python
from harnice.lists import manifest
```
 then use as written.*
??? info "`manifest.new()`"

    Synchronize the system harness manifest with the system connector list:
      - Remove nets that no longer exist in the connector list
      - Add nets that appear in the connector list but not yet in the manifest
      - Preserve all other column data for nets that still exist

??? info "`manifest.update_upstream()`"

    Documentation needed.

??? info "`manifest.new()`"

    Synchronize the system harness manifest with the system connector list:
      - Remove nets that no longer exist in the connector list
      - Add nets that appear in the connector list but not yet in the manifest
      - Preserve all other column data for nets that still exist

??? info "`manifest.update_upstream()`"

    Documentation needed.

