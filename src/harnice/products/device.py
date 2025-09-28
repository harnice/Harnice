import os
import runpy
from harnice import fileio, icd, rev_history
import sexpdata
import json

device_feature_tree_default = """
from harnice import icd

ch_type_ids = {
    "in": (1, "https://github.com/kenyonshutt/harnice-library-public"),
    "out": (4, "https://github.com/kenyonshutt/harnice-library-public"),
    "chassis": (5, "https://github.com/kenyonshutt/harnice-library-public")
}

xlr_pinout = {
    "pos": 2,
    "neg": 3,
    "chassis": 1
}

connector_mpns = {
    "XLR3F": ["in1", "in2"],
    "XLR3M": ["out1", "out2"]
}

def mpn_for_connector(connector_name):
    for mpn, conn_list in connector_mpns.items():
        if connector_name in conn_list:
            return mpn
    return None

icd.new_signals_list("device")

for connector_name in ["in1", "in2", "out1", "out2"]:
    if connector_name.startswith("in"):
        channel_type_id = ch_type_ids["in"]
    elif connector_name.startswith("out"):
        channel_type_id = ch_type_ids["out"]
    else:
        continue

    channel_name = connector_name
    connector_mpn = mpn_for_connector(connector_name)

    for signal in icd.signals_of_channel_type_id(channel_type_id):
        icd.write_signal(
            channel=channel_name,
            signal=signal,
            connector_name=connector_name,
            contact=xlr_pinout.get(signal),
            channel_type_id=channel_type_id,
            connector_mpn=connector_mpn
        )

    # Add shield row
    icd.write_signal(
        channel=f"{channel_name}-shield",
        signal="chassis",
        connector_name=connector_name,
        contact=xlr_pinout.get("chassis"),
        channel_type_id=ch_type_ids["chassis"],
        connector_mpn=connector_mpn
    )

"""


def make_new_library_file():
    """Create a bare .kicad_sym file with only library header info."""

    symbol_lib = [
        sexpdata.Symbol("kicad_symbol_lib"),
        [sexpdata.Symbol("version"), 20241209],
        [sexpdata.Symbol("generator"), "kicad_symbol_editor"],
        [sexpdata.Symbol("generator_version"), "9.0"],
    ]

    with open(fileio.path("library file"), "w", encoding="utf-8") as f:
        sexpdata.dump(symbol_lib, f, pretty=True)


def parse_kicad_sym_file():
    """
    Load a KiCad .kicad_sym file and return its parsed sexp data.
    """
    with open(fileio.path("library file"), "r", encoding="utf-8") as f:
        data = sexpdata.load(f)
    return data


def symbol_exists(kicad_library_data, target_symbol_name):
    """
    Check if a symbol with a given name exists in a KiCad library.

    Args:
        kicad_library_data: Parsed sexpdata of the .kicad_sym file.
        target_symbol_name: The symbol name string to search for.

    Returns:
        True if the symbol exists, False otherwise.
    """
    for element in kicad_library_data:
        # Each element could be a list like: ["symbol", "sym_name", ...]
        if isinstance(element, list) and len(element) > 1:
            if element[0] == sexpdata.Symbol("symbol"):
                if str(element[1]) == target_symbol_name:
                    return True
    return False


def make_property(name, value, id_counter=None, hide=False):
    # adds a property to the current rev symbol of the library
    builtins = {"Reference", "Value", "Footprint", "Datasheet", "Description"}
    prop = [
        sexpdata.Symbol("property"),
        name,
        value,  # always a string
    ]
    if name not in builtins:
        if id_counter is None:
            raise ValueError(f"Custom property {name} requires an id_counter")
        prop.append([sexpdata.Symbol("id"), id_counter])
    prop.append([sexpdata.Symbol("at"), 0, 0, 0])
    effects = [
        sexpdata.Symbol("effects"),
        [sexpdata.Symbol("font"), [sexpdata.Symbol("size"), 1.27, 1.27]],
    ]
    if hide:
        effects.append([sexpdata.Symbol("hide"), sexpdata.Symbol("yes")])
    prop.append(effects)
    return prop


def add_blank_symbol(sym_name, value="", footprint="", datasheet="", description=""):
    """Append a blank symbol into the .kicad_sym at fileio.path('library file')."""

    lib_path = fileio.path("library file")

    # Load the existing s-expression
    with open(lib_path, "r", encoding="utf-8") as f:
        data = sexpdata.load(f)

    # Build symbol s-expression
    symbol = [
        sexpdata.Symbol("symbol"),
        sym_name,
        [sexpdata.Symbol("exclude_from_sim"), sexpdata.Symbol("no")],
        [sexpdata.Symbol("in_bom"), sexpdata.Symbol("yes")],
        [sexpdata.Symbol("on_board"), sexpdata.Symbol("yes")],
        make_property("Reference", get_attribute("default_refdes")),
        make_property("Value", value),
        make_property("Footprint", footprint, hide=True),
        make_property("Datasheet", datasheet, hide=True),
        make_property("Description", get_attribute("desc"), hide=True),
        make_property("MFG", get_attribute("manufacturer"), hide=False, id_counter=0),
        make_property(
            "MPN", get_attribute("manufacturer_part_number"), hide=False, id_counter=1
        ),
        make_property(
            "lib_repo", get_attribute("library_repo"), hide=True, id_counter=2
        ),
        make_property(
            "lib_subpath", get_attribute("library_subpath"), hide=True, id_counter=3
        ),
        make_property("rev", fileio.partnumber("rev"), hide=True, id_counter=4),
        [sexpdata.Symbol("embedded_fonts"), sexpdata.Symbol("no")],
    ]

    # Append to the library data
    data.append(symbol)

    # Write back out
    with open(lib_path, "w", encoding="utf-8") as f:
        sexpdata.dump(data, f, pretty=True)


def overwrite_or_create_property_in_symbol(prop_name, value, hide=False):
    """
    Overwrite or create a property inside the target symbol block
    in the KiCad .kicad_sym library file.

    - File is always fileio.path("library file")
    - Symbol to modify is always named fileio.partnumber("pn-rev")

    Args:
        prop_name (str): Name of the property
        value (str): Value to set (will always be forced to string)
        hide (bool): Whether to hide the property
    """

    target_symbol_name = fileio.partnumber("pn-rev")

    # Ensure value is a string (KiCad requirement)
    if value is None:
        value = ""
    else:
        value = str(value)

    # Load the library file
    with open(fileio.path("library file"), "r", encoding="utf-8") as f:
        data = sexpdata.load(f)

    def next_id(symbol):
        """Find the next available id number among custom properties."""
        max_id = -1
        for elem in symbol:
            if (
                isinstance(elem, list)
                and len(elem) >= 4
                and isinstance(elem[0], sexpdata.Symbol)
                and elem[0].value() == "property"
            ):
                for sub in elem:
                    if isinstance(sub, list) and len(sub) == 2:
                        if (
                            isinstance(sub[0], sexpdata.Symbol)
                            and sub[0].value() == "id"
                            and isinstance(sub[1], int)
                        ):
                            max_id = max(max_id, sub[1])
        return max_id + 1

    def overwrite_or_create(symbol):
        # Try to overwrite existing property
        for elem in symbol:
            if (
                isinstance(elem, list)
                and len(elem) >= 3
                and isinstance(elem[0], sexpdata.Symbol)
                and elem[0].value() == "property"
                and elem[1] == prop_name
            ):
                elem[2] = value  # force overwrite as string
                return symbol

        # If missing, create new one with next id
        new_id = next_id(symbol)
        new_prop = make_property(prop_name, value, id_counter=new_id, hide=hide)
        symbol.append(new_prop)
        return symbol

    # Traverse to the right (symbol ...) block
    for i, elem in enumerate(data):
        if (
            isinstance(elem, list)
            and isinstance(elem[0], sexpdata.Symbol)
            and elem[0].value() == "symbol"
            and elem[1] == target_symbol_name
        ):
            data[i] = overwrite_or_create(elem)

    # Save file back
    with open(fileio.path("library file"), "w", encoding="utf-8") as f:
        sexpdata.dump(data, f)


def extract_pins_from_symbol(kicad_lib, symbol_name):
    """
    Extract all pin info for the given symbol (and its subsymbols).
    Returns a list of dicts like {"name": ..., "number": ..., "type": ..., "shape": ...}.
    """

    def sym_to_str(obj):
        """Convert sexpdata.Symbol to string, pass through everything else."""
        if isinstance(obj, sexpdata.Symbol):
            return obj.value()
        return obj

    pins = []

    def recurse(node, inside_target=False):
        if not isinstance(node, list) or not node:
            return

        tag = sym_to_str(node[0])

        if tag == "symbol":
            sym_name = sym_to_str(node[1])
            new_inside = inside_target or (sym_name == symbol_name)
            for sub in node[2:]:
                recurse(sub, inside_target=new_inside)

        elif tag == "pin" and inside_target:
            pin_type = sym_to_str(node[1]) if len(node) > 1 else None
            pin_shape = sym_to_str(node[2]) if len(node) > 2 else None
            name_val = None
            number_val = None

            for entry in node[3:]:
                if isinstance(entry, list) and entry:
                    etag = sym_to_str(entry[0])
                    if etag == "name":
                        name_val = sym_to_str(entry[1])
                    elif etag == "number":
                        number_val = sym_to_str(entry[1])

            pin_info = {
                "name": name_val,
                "number": number_val,
                "type": pin_type,
                "shape": pin_shape,
            }
            pins.append(pin_info)

        else:
            for sub in node[1:]:
                recurse(sub, inside_target=inside_target)

    recurse(kicad_lib, inside_target=False)
    return pins


def validate_pins(pins, unique_connectors_in_signals_list):
    """Validate pins for uniqueness, type conformity, and check required pins.

    Returns:
        tuple:
            missing (set): Any missing pin names from unique_connectors_in_signals_list.
            used_pin_numbers (set): Numbers already assigned to pins.
    Raises:
        ValueError: On duplicate names/numbers or invalid types.
    """
    seen_names = set()
    seen_numbers = set()

    for pin in pins:
        name = pin.get("name")
        number = pin.get("number")
        ptype = pin.get("type")

        # Duplicate name
        if name in seen_names:
            raise ValueError(f"Duplicate pin name found: {name}")
        seen_names.add(name)

        # Duplicate number
        if number in seen_numbers:
            raise ValueError(f"Duplicate pin number found: {number}")
        seen_numbers.add(number)

        # Type check
        if ptype != "unspecified":
            raise ValueError(
                f"Pin {name} ({number}) has invalid type: {ptype}. Harnice requires all pins to have type 'unspecified'."
            )

    # Set comparison for 1:1 match
    required = set(unique_connectors_in_signals_list)
    pin_names = seen_names

    missing = required - pin_names
    extra = pin_names - required
    if extra:
        raise ValueError(
            f"The following pin(s) exist in KiCad symbol but not Signals List: {', '.join(sorted(extra))}"
        )

    return missing, seen_numbers


def append_missing_pin(pin_name, pin_number, spacing=3.81):
    """
    Append a pin to a KiCad symbol if it's missing, auto-spacing vertically.
    Immediately writes the updated symbol back to fileio.path("library file").

    Args:
        pin_name (str): name of the pin.
        pin_number (str or int): number of the pin.
        spacing (float): vertical spacing in mm (default 3.81mm).

    Returns:
        list: Updated symbol_data (sexpdata structure).
    """
    file_path = fileio.path("library file")
    pin_number = str(pin_number)

    # --- Load latest file contents ---
    with open(file_path, "r", encoding="utf-8") as f:
        symbol_data = sexpdata.load(f)

    # --- Find the main symbol ---
    top_symbol = None
    sub_symbol = None
    for item in symbol_data:
        if (
            isinstance(item, list)
            and len(item) > 0
            and isinstance(item[0], sexpdata.Symbol)
        ):
            if item[0].value() == "symbol":
                top_symbol = item
                for sub in item[1:]:
                    if isinstance(sub, list) and isinstance(sub[0], sexpdata.Symbol):
                        if sub[0].value() == "symbol":
                            sub_symbol = sub
                            break

    # fallback: use top-level symbol if no sub-symbol found
    target_symbol = sub_symbol if sub_symbol is not None else top_symbol
    if target_symbol is None:
        raise ValueError("No symbol found in file to append pins into.")

    # --- Check for duplicates ---
    for elem in target_symbol[1:]:
        if (
            isinstance(elem, list)
            and isinstance(elem[0], sexpdata.Symbol)
            and elem[0].value() == "pin"
        ):
            name_entry = next(
                (
                    x
                    for x in elem
                    if isinstance(x, list)
                    and isinstance(x[0], sexpdata.Symbol)
                    and x[0].value() == "name"
                ),
                None,
            )
            num_entry = next(
                (
                    x
                    for x in elem
                    if isinstance(x, list)
                    and isinstance(x[0], sexpdata.Symbol)
                    and x[0].value() == "number"
                ),
                None,
            )
            if (
                name_entry
                and name_entry[1] == pin_name
                and num_entry
                and num_entry[1] == pin_number
            ):
                return symbol_data  # already present, no write needed

    # --- Find max Y among existing pins ---
    max_y = -spacing  # ensures first pin goes at 0 if none exist
    for elem in target_symbol[1:]:
        if (
            isinstance(elem, list)
            and isinstance(elem[0], sexpdata.Symbol)
            and elem[0].value() == "pin"
        ):
            at_entry = next(
                (
                    x
                    for x in elem
                    if isinstance(x, list)
                    and isinstance(x[0], sexpdata.Symbol)
                    and x[0].value() == "at"
                ),
                None,
            )
            if at_entry and len(at_entry) >= 3:
                y_val = float(at_entry[2])
                if y_val > max_y:
                    max_y = y_val

    new_y = max_y + spacing

    # --- Build new pin block (all keywords as Symbols) ---
    new_pin = [
        sexpdata.Symbol("pin"),
        sexpdata.Symbol("unspecified"),
        sexpdata.Symbol("line"),
        [sexpdata.Symbol("at"), 0, new_y, 0],
        [sexpdata.Symbol("length"), 2.54],
        [
            sexpdata.Symbol("name"),
            pin_name,
            [
                sexpdata.Symbol("effects"),
                [sexpdata.Symbol("font"), [sexpdata.Symbol("size"), 1.27, 1.27]],
            ],
        ],
        [
            sexpdata.Symbol("number"),
            pin_number,
            [
                sexpdata.Symbol("effects"),
                [sexpdata.Symbol("font"), [sexpdata.Symbol("size"), 1.27, 1.27]],
            ],
        ],
    ]

    target_symbol.append(new_pin)

    # --- Write updated symbol back to file ---
    with open(file_path, "w", encoding="utf-8") as f:
        sexpdata.dump(symbol_data, f)

    print(f"Appended pin {pin_name} ({pin_number}) to {fileio.partnumber('pn-rev')}")

    return symbol_data


def next_free_number(seen_numbers, start=1):
    """Find the next unused pin number as a string."""
    n = start
    while True:
        if str(n) not in seen_numbers:
            return str(n)
        n += 1


def validate_kicad_library():
    """
    Validate that the KiCad .kicad_sym library has:
    0. The .kicad_sym file exists (create if missing).
    1. A symbol matching the current part number.
    2. Pins that match the connectors in the signals list.
    """

    if not os.path.exists(fileio.path("library file")):
        print(f"Making a new Kicad symbol at {fileio.path("library file")}")
        make_new_library_file()

    kicad_library_data = parse_kicad_sym_file()

    if not symbol_exists(kicad_library_data, fileio.partnumber("pn-rev")):
        add_blank_symbol(
            sym_name=fileio.partnumber("pn-rev"),
        )

    # Step 1. Collect unique connectors from the signals list
    unique_connectors_in_signals_list = set()
    for signal in icd.read_signals_list():
        connector_name = signal.get("connector_name")
        if connector_name:
            unique_connectors_in_signals_list.add(connector_name)

    # Step 2. Validate pins
    kicad_lib = parse_kicad_sym_file()
    pins = extract_pins_from_symbol(kicad_lib, fileio.partnumber("pn-rev"))
    missing, seen_numbers = validate_pins(pins, unique_connectors_in_signals_list)

    kicad_library_data = parse_kicad_sym_file()

    # Step 3. Append missing pins
    for pin_name in missing:
        # find the next available number
        pin_number = next_free_number(seen_numbers)
        # append it
        append_missing_pin(pin_name, pin_number)
        # mark number as used
        seen_numbers.add(pin_number)

    # Step 4. Overwrite symbol properties
    overwrite_or_create_property_in_symbol(
        "Reference", get_attribute("default_refdes"), hide=False
    )
    overwrite_or_create_property_in_symbol(
        "Description", get_attribute("desc"), hide=False
    )
    overwrite_or_create_property_in_symbol("MFG", get_attribute("mfg"), hide=True)
    overwrite_or_create_property_in_symbol("MPN", get_attribute("pn"), hide=False)
    overwrite_or_create_property_in_symbol(
        "lib_repo", get_attribute("library_repo"), hide=True
    )
    overwrite_or_create_property_in_symbol(
        "lib_subpath", get_attribute("library_subpath"), hide=True
    )
    overwrite_or_create_property_in_symbol("rev", fileio.partnumber("rev"), hide=True)


def validate_attributes_json():
    """Ensure an attributes JSON file exists with default values if missing."""

    default_attributes = {"default_refdes": "DEVICE"}

    attributes_path = fileio.path("attributes")

    # If attributes file does not exist, create it with defaults
    if not os.path.exists(attributes_path):
        with open(attributes_path, "w", encoding="utf-8") as f:
            json.dump(default_attributes, f, indent=4)

    # If it exists, load it and verify required keys
    else:
        with open(attributes_path, "r", encoding="utf-8") as f:
            try:
                attributes = json.load(f)
            except json.JSONDecodeError:
                raise ValueError(f"Invalid JSON in attributes file: {attributes_path}")

        updated = False
        for key, value in default_attributes.items():
            if key not in attributes:
                attributes[key] = value
                updated = True

        if updated:
            with open(attributes_path, "w", encoding="utf-8") as f:
                json.dump(attributes, f, indent=4)
            print(f"Updated attributes file with missing defaults at {attributes_path}")


def get_attribute(attribute_key):
    # find an attribute from either revision history tsv or attributes json
    if attribute_key in rev_history.revision_history_columns():
        revision_info = rev_history.revision_info()
        return revision_info.get(attribute_key)

    else:
        with open(fileio.path("attributes"), "r", encoding="utf-8") as f:
            return json.load(f).get(attribute_key)


def device_render(lightweight=False):
    fileio.verify_revision_structure(product_type="device")
    fileio.generate_structure()

    validate_attributes_json()

    if not lightweight:
        if not os.path.exists(fileio.path("signals list")):
            with open(fileio.path("feature tree"), "w", encoding="utf-8") as f:
                f.write(device_feature_tree_default)
    else:
        if not os.path.exists(fileio.path("signals list")):
            icd.new_signals_list()
            icd.write_signal(
                connector_name="J1",
                channel_type_id=0,
                signal="placeholder",
                contact=1,
                connector_mpn="DB9_F",
            )

    if os.path.exists(fileio.path("feature tree")):
        runpy.run_path(fileio.path("feature tree"))
        print("Successfully rebuilt signals list per feature tree.")

    if not lightweight:
        icd.validate_signals_list_for_device()

    print(
        f"Kicad nickname:       harnice-devices/{rev_history.revision_info().get('library_subpath')}{fileio.partnumber('pn')}"
    )

    validate_kicad_library()


def lightweight_render():
    device_render(lightweight=True)


def render():
    device_render(lightweight=False)
