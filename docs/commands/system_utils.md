# System Utilities
---
##Commands:
*Use the following functions by first importing the module in your script like this: 
```python
from harnice.lists import system_utils
```
 then use as written.*
??? info "`system_utils.mpn_of_device_refdes()`"

    documentation needed

??? info "`system_utils.connector_of_channel()`"

    documentation needed

??? info "`system_utils.find_connector_with_no_circuit()`"

    documentation needed

??? info "`system_utils.make_instances_for_connectors_cavities_nodes_channels_circuits()`"

    documentation needed

??? info "`system_utils.add_chains_to_channel_map()`"

    For each (from_device/channel) -> (to_device/channel) in the channel map,
    find:
      - 'disconnect_refdes_requirement' (like "X1(A,B);X2(B,A)")
      - 'chain_of_nets' (like "WH-1;WH-2;WH-3" or a single net if no disconnects)
      - 'chain_of_connectors' (like "WH-1.J1A;WH-2.X1A;WH-2.X1B;WH-3.J2A")

??? info "`system_utils.make_instances_from_bom()`"

    documentation needed

