# Interacting with Revision History Lists
A record of every revision of a part, and its release status

---
##Columns 
*Columns are automatically generated when `rev_history.new()` is called. Additional columns are not supported and may result in an error when parsing.*
=== "`product`"

    the harnice product type (e.g. "harness", "connector", "device", "system", "macro", "flagnote", "tblock")

=== "`mfg`"

    who manufactures this product (blank ok)

=== "`pn`"

    name, part number, other identifier of this part. mfg+mpn combination must be unique within the library.

=== "`desc`"

    a brief description of this product

=== "`rev`"

    the revision of the part

=== "`status`"

    "released", "obsolete", etc. Harnice will not render a revision if the status has text in this field as a form of protection.

=== "`releaseticket`"

    many companies do this, but it's not required.

=== "`library_repo`"

    auto-filled on render if the current working directory is discovered to be a library repository.

=== "`library_subpath`"

    auto-filled on render if in a library repository, this is the chain of directories between the product type and the part number

=== "`datestarted`"

    auto-filled to be the date when this part was first intialized

=== "`datemodified`"

    updates to today's date upon rendering

=== "`datereleased`"

    up to user to fill in as needed

=== "`git_hash_of_harnice_src`"

    auto-filled, git hash of the harnice source code during the latest render

=== "`drawnby`"

    auto-filled, the person who created the part

=== "`checkedby`"

    the person who checked the part, blank ok

=== "`revisionupdates`"

    a brief description of the changes made to this revision

=== "`affectedinstances`"

    the instance names of the instances that were affected by this revision. can be referenced later by PDF builders and more.


---
##Commands:
*Use the following functions by first importing the module in your script like this: 
```python
from harnice.lists import rev_history
```
 then use as written.*
??? info "`rev_history.overwrite(content_dict)`"

    Overwrite a revision history entry.
    
    **Arguments:**
    
     - `content_dict` (dict): The content to overwrite the revision history entry with.
        - This should be a dictionary with the keys and values to overwrite.
        - The keys should be the column names, and the values should be the new values.
        - Some keys are protected and cannot be overwritten:
            - `"product"`
            - `"mfg"`
            - `"pn"`
            - `"rev"`
            - `"releaseticket"`
            - `"library_repo"`
            - `"library_subpath"`
            - `"datestarted"`
    
    The function will update the revision history file as referenced by the current product file structure.
    
    **Returns:**
    
     - `None`
    
    **Raises:**
    
     - `KeyError`: If a key is provided that is not in the COLUMNS list.
     - `KeyError`: If a protected key is provided.
     - `ValueError`: If the revision history file is not found.
     - `ValueError`: If the revision is not found in the revision history file.
     - `RuntimeError`: If `state.rev` is not set.

??? info "`rev_history.info(rev=None, path=None, field=None, all=False)`"

    Get information about a revision history entry.
    
    **Arguments:**
    
    - `rev` (str): The revision to get information about.
    - `path` (str): The path to the revision history file.
        - If not provided, the function will use the default path: `"revision history"`.
    - `field` (str): The field to get information about.
        - If not provided, the function will return the entire row.
        - If provided, the function will return the value of the field.
    - `all` (bool): If `True`, return all rows.
        - If not provided, the function will return the first row.
    
    **Returns:**
    
    - `dict`: The row of the revision history entry (when `field` is not provided).
    - `list`: A list of all rows in the revision history file (when `all=True`).
    - `str`: The value of the field (when `field` is provided).
    
    **Raises:**
    
    - `FileNotFoundError`: If the revision history file is not found.
    - `ValueError`: If the revision is not found in the revision history file.

??? info "`rev_history.initial_release_exists()`"

    Check if an initial release exists.
    
    **Arguments:**
    
    None
    
    **Returns:**
    
    - `bool`: `True` if a revision with the text `"INITIAL RELEASE"` in the `"revisionupdates"` field exists, `False` otherwise.

??? info "`rev_history.initial_release_desc()`"

    Get the description of the initial release.
    
    **Arguments:**
    
    None
    
    **Returns:**
    
    - `str`: The description of the revision which has `revisionupdates == 'INITIAL RELEASE'`.

??? info "`rev_history.update_datemodified()`"

    Update the `datemodified` field of the current revision with today's date.
    
    **Arguments:**
    
    None
    
    **Returns:**
    
    - `None`
    
    **Raises:**
    
    - `ValueError`: If the revision history file is not found.
    - `ValueError`: If the revision is not found in the revision history file.

??? info "`rev_history.new(ignore_product=False, path=None)`"

    Create a new revision history file.
    
    **Arguments:**
    
    - `ignore_product` (bool):
        - If `True`, the function will raise an error if `state.product` is not set first.
        - If `False`, the function will prompt the user to select a product type.
    
    **Returns:**
    
    - `None`
    
    **Raises:**
    
    - `ValueError`: If attempting to create a new revision history file without a product type when `ignore_product=True`.
    - `ValueError`: If attempting to overwrite an existing revision history file.

??? info "`rev_history.append(next_rev=None)`"

    Append a new revision history entry to the current revision history file.
    
    If the revision history file does not exist, the function will create it.
    If the revision history file exists, the function will append a new entry to the file.
    
    It will prompt the user for the following fields:
    
    - `product`: The product type of the part.
    - `desc`: The description of the part.
    - `revisionupdates`: What is the purpose of this revision?
    
    If the previous revision has a blank status, the function will prompt the user to obsolete it with a message.
    
    **Arguments:**
    
    - `next_rev` The next revision number to append.
    
    **Returns:**
    
    - `None`

??? info "`rev_history.part_family_append(content_dict, rev_history_path)`"

    Append a new revision history entry to the part family revision history file.
    
    Intended to be called by part family scripts only.
    
    The function will automatically update the following fields in the content dictionary:
    
    - `datemodified`: Set to today's date
    - `drawnby`: Set to the current user's name
    - `git_hash_of_harnice_src`: Set to the current git hash of the harnice source code
    
    If the revision history file does not exist, the function will create it.
    If an entry with the same revision number already exists, the function will update that entry.
    Otherwise, the function will append a new entry to the file.
    
    **Arguments:**
    
    - `content_dict` (dict): The content to append to the part family revision history file.
        - Should contain keys matching the `COLUMNS` list.
        - The `rev` key is used to determine if an entry already exists.
    - `rev_history_path` (str): The path to the part family revision history file.
    
    **Returns:**
    
    - `None`
    
    **Raises:**
    
    - `ValueError`: If the content dictionary contains invalid keys or missing required fields.

