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

    Assigns sequential numbers to build note instances.
    
    Iterates through all note instances in the instances list and assigns sequential
    numbers to build notes. Each build note gets a unique number and that number is
    set as both the `note_number` and `print_name` fields.

??? info "`note_utils.make_rev_history_notes()`"

    Creates revision change callout notes based on revision history.
    
    Creates a revision change callout note for a given revision, linking it to
    the instances affected by that revision. The note text comes from the
    revision's update description.
    
    **Args:**
    - `rev` (dict): Revision dictionary from revision history containing at least
        `'rev'` and `'revisionupdates'` fields.

??? info "`note_utils.make_bom_flagnote()`"

    Creates a BOM item flagnote dictionary for an instance.
    
    Creates a flagnote configuration dictionary that displays the BOM line number
    for a given instance. The flagnote is positioned at the specified output
    coordinate system of the instance.
    
    **Args:**
    - `affected_instance` (dict): Instance dictionary to create a flagnote for.
    - `output_csys_name` (str): Name of the output coordinate system where the
        flagnote should be positioned.
    
    **Returns:**
    - `dict`: A flagnote instance dictionary ready to be added to the instances list.

??? info "`note_utils.make_part_name_flagnote()`"

    Creates a part name flagnote dictionary for an instance.
    
    Creates a flagnote configuration dictionary that displays the print name
    of a given instance. The flagnote is positioned at the specified output
    coordinate system of the instance.
    
    **Args:**
    - `affected_instance` (dict): Instance dictionary to create a flagnote for.
    - `output_csys_name` (str): Name of the output coordinate system where the
        flagnote should be positioned.
    
    **Returns:**
    - `dict`: A flagnote instance dictionary ready to be added to the instances list.

??? info "`note_utils.make_buildnote_flagnote()`"

    Creates a build note flagnote dictionary linking a note to an instance.
    
    Creates a flagnote configuration dictionary that displays a build note on
    a specific instance. The flagnote shows the build note's print name and is
    positioned at the specified output coordinate system of the affected instance.
    
    **Args:**
    - `note_instance` (dict): Build note instance dictionary.
    - `affected_instance` (dict): Instance dictionary to attach the flagnote to.
    - `output_csys_name` (str): Name of the output coordinate system where the
        flagnote should be positioned.
    
    **Returns:**
    - `dict`: A flagnote instance dictionary ready to be added to the instances list.

??? info "`note_utils.make_rev_change_flagnote()`"

    Creates a revision change callout flagnote dictionary linking a note to an instance.
    
    Creates a flagnote configuration dictionary that displays a revision change
    callout note on a specific instance. The flagnote shows the revision number
    and is positioned at the specified output coordinate system of the affected instance.
    
    **Args:**
    - `note_instance` (dict): Revision change callout note instance dictionary.
    - `affected_instance` (dict): Instance dictionary to attach the flagnote to.
    - `output_csys_name` (str): Name of the output coordinate system where the
        flagnote should be positioned.
    
    **Returns:**
    - `dict`: A flagnote instance dictionary ready to be added to the instances list.

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

    Combines multiple notes by merging their affected instances into one note.
    
    Merges one or more notes into a single note by combining their affected instances
    lists. The note to keep is identified by `keep_note_text`, and all notes matching
    `merge_note_texts` are merged into it and then removed.
    
    **Args:**
    - `keep_note_text` (str): The `note_text` value of the note to keep and merge others into.
    - `merge_note_texts` (list): List of `note_text` values to find and merge into the kept note.
    - `note_type` (list, optional): If provided, only notes with `note_type` in this list
        will be considered for merging. If `None`, all notes are considered.

