# Interacting with Disconnect Maps
A list of every available channel on a every disconnect, and every channel that may or may not pass through it

---
##Columns 
*Columns are automatically generated when `disconnect_map.new()` is called. Additional columns are not supported and may result in an error when parsing.*
=== "`A-side_device_refdes`"

    documentation needed

=== "`A-side_device_channel_id`"

    documentation needed

=== "`A-side_device_channel_type`"

    documentation needed

=== "`B-side_device_refdes`"

    documentation needed

=== "`B-side_device_channel_id`"

    documentation needed

=== "`B-side_device_channel_type`"

    documentation needed

=== "`disconnect_refdes`"

    documentation needed

=== "`disconnect_channel_id`"

    documentation needed

=== "`A-port_channel_type`"

    documentation needed

=== "`B-port_channel_type`"

    documentation needed

=== "`manual_map_channel_python_equiv`"

    documentation needed


---
##Commands:
*Use the following functions by first importing the module in your script like this: 
```python
from harnice.lists import disconnect_map
```
 then use as written.*
??? info "`disconnect_map.new()`"

    Documentation needed.

??? info "`disconnect_map.assign(a_side_key, disconnect_key)`"

    Documentation needed.

??? info "`disconnect_map.already_assigned_channels_through_disconnects_set_append(key, disconnect_refdes)`"

    Documentation needed.

??? info "`disconnect_map.already_assigned_disconnects_set_append(key)`"

    Documentation needed.

??? info "`disconnect_map.already_assigned_channels_through_disconnects_set()`"

    Documentation needed.

??? info "`disconnect_map.already_assigned_disconnects_set()`"

    Documentation needed.

??? info "`disconnect_map.channel_is_already_assigned_through_disconnect(key, disconnect_refdes)`"

    Documentation needed.

??? info "`disconnect_map.disconnect_is_already_assigned(key)`"

    Documentation needed.

??? info "`disconnect_map.ensure_requirements_met()`"

    Documentation needed.

