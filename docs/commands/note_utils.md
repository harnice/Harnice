# Note Utilities
---
##Commands:
*Use the following functions by first importing the module in your script like this: 
```python
from harnice.lists import note_utils
```
 then use as written.*
??? info "`note_utils.new_note()`"

    Creates or updates a note instance.
    
    Behavior:
    - If a note with identical (note_type, note_text) already exists:
        * If either existing or new affectedinstances is empty → ERROR.
        * Else → merge affectedinstances into existing note, DO NOT create a new one.

??? info "`note_utils.assign_buildnote_numbers()`"

    documentation needed

??? info "`note_utils.make_rev_history_notes()`"

    documentation needed

??? info "`note_utils.make_bom_flagnote()`"

    documentation needed

??? info "`note_utils.make_part_name_flagnote()`"

    documentation needed

??? info "`note_utils.make_buildnote_flagnote()`"

    documentation needed

??? info "`note_utils.make_rev_change_flagnote()`"

    documentation needed

??? info "`note_utils.parse_note_instance()`"

    Return a full copy of `instance`, but with note_affected_instances
    parsed into a real Python list (or left alone if blank).

??? info "`note_utils.get_lib_build_notes()`"

    Returns list of build_notes for this instance from the TSV row.
    Safely parses with ast.literal_eval.
    Always returns a Python list.

??? info "`note_utils.get_lib_tools()`"

    Returns list of tools for this instance from the TSV row.
    Safely parses with ast.literal_eval.
    Always returns a Python list.

??? info "`note_utils.combine_notes()`"

    documentation needed

