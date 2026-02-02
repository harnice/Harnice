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

    Documentation needed.

??? info "`rev_history.info(rev=None, path=None, field=None, all=False)`"

    Documentation needed.

??? info "`rev_history.initial_release_exists()`"

    Documentation needed.

??? info "`rev_history.initial_release_desc()`"

    Documentation needed.

??? info "`rev_history.update_datemodified()`"

    Documentation needed.

??? info "`rev_history.new()`"

    Documentation needed.

??? info "`rev_history.append(next_rev=None)`"

    Documentation needed.

