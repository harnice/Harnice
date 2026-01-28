# System Utilities
---
##Commands:
*Use the following functions by first importing the module in your script like this: 
```python
from harnice.lists import system_utils
```
 then use as written.*
??? info "`system_utils.mpn_of_device_refdes(refdes)`"

    Looks up manufacturer part number information for a device reference designator.
    
    Searches the BOM (Bill of Materials) for a device with the given reference designator
    and returns its manufacturer, part number, and revision.
    
    **Args:**
    - `refdes` (str): Device reference designator to look up (e.g., `"J1"`, `"X1"`).
    
    **Returns:**
    - `tuple`: A tuple of `(MFG, MPN, rev)` if found, or `(None, None, None)` if not found.

??? info "`system_utils.connector_of_channel(key)`"

    Finds the connector name associated with a device channel.
    
    Given a device reference designator and channel ID tuple, looks up the corresponding
    connector name from the device's signals list.
    
    **Args:**
    - `key` (tuple): A tuple of `(device_refdes, channel_id)` identifying the channel.
    
    **Returns:**
    - `str`: The connector name associated with the channel.
    
    **Raises:**
    - `ValueError`: If the connector is not found for the given channel.

??? info "`system_utils.find_connector_with_no_circuit(connector_list, circuits_list)`"

    Validates that all connectors have associated circuits.
    
    Checks each connector in the connector list to ensure it has at least one
    corresponding circuit in the circuits list. Skips connectors with `"unconnected"`
    in their net name. Raises an error if any connector lacks a circuit.
    
    **Args:**
    - `connector_list` (list): List of connector dictionaries from the system connector list.
    - `circuits_list` (list): List of circuit dictionaries from the circuits list.
    
    **Raises:**
    - `ValueError`: If a connector is found that has no associated circuits. The error
        message suggests checking the channel map and channel compatibility.

??? info "`system_utils.make_instances_for_connectors_cavities_nodes_channels_circuits()`"

    Creates instances for all system components based on circuits.
    
    This function processes the circuits list and creates instances in the instances list
    for all connectors, connector cavities, nodes, channels, and circuits in the system.
    For each circuit, it creates:
    
    - Connector nodes (at both ends)
    - Connector instances (at both ends)
    - Connector cavity instances (at both ends)
    - Circuit instance
    - Channel instance
    - Net-channel instances for each net in the channel chain
    
    The function reads from the circuits list, system connector list, and channel map
    to build the complete instance hierarchy.

??? info "`system_utils.add_chains_to_channel_map()`"

    For each (from_device/channel) -> (to_device/channel) in the channel map,
    find:
      - 'disconnect_refdes_requirement' (like "X1(A,B);X2(B,A)")
      - 'chain_of_nets' (like "WH-1;WH-2;WH-3" or a single net if no disconnects)
      - 'chain_of_connectors' (like "WH-1.J1A;WH-2.X1A;WH-2.X1B;WH-3.J2A")

??? info "`system_utils.make_instances_from_bom()`"

    Creates instances for all devices and disconnects from the BOM.
    
    Reads the Bill of Materials (BOM) and imports each device or disconnect into the
    instances list using `library_utils.pull()`. Each item is imported with its manufacturer,
    part number, revision, and library information.
    
    Items with the `"disconnect"` field set are imported as type `"disconnect"`,
    all others are imported as type `"device"`.

