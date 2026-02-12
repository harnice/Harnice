import os
import runpy
import sexpdata
import json
import csv
from harnice import fileio, state
from harnice.lists import signals_list, rev_history
from harnice.products import chtype

default_desc = "DEVICE, FUNCTION, ATTRIBUTES, etc."

device_feature_tree_utils_default = """
from harnice.lists import signals_list
from harnice.products import chtype

ch_type_ids = {
    "in": (1, "https://github.com/harnice/harnice"),
    "out": (4, "https://github.com/harnice/harnice"),
    "chassis": (5, "https://github.com/harnice/harnice")
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

signals_list.new()

for connector_name in ["in1", "in2", "out1", "out2"]:
    if connector_name.startswith("in"):
        channel_type = ch_type_ids["in"]
    elif connector_name.startswith("out"):
        channel_type = ch_type_ids["out"]
    else:
        continue

    channel_name = connector_name
    connector_mpn = mpn_for_connector(connector_name)

    for signal in chtype.signals(channel_type):
        signals_list.append(
            channel_id=channel_name,
            signal=signal,
            connector_name=connector_name,
            cavity=xlr_pinout.get(signal),
            channel_type=channel_type,
            connector_mpn=connector_mpn
        )

    # Add shield row
    signals_list.append(
        channel_id=f"{channel_name}-shield",
        signal="chassis",
        connector_name=connector_name,
        cavity=xlr_pinout.get("chassis"),
        channel_type=ch_type_ids["chassis"],
        connector_mpn=connector_mpn
    )

"""


def file_structure():
    return {
        f"{state.partnumber('pn-rev')}-feature_tree.py": "feature tree",
        f"{state.partnumber('pn-rev')}-signals_list.tsv": "signals list",
        f"{state.partnumber('pn-rev')}-attributes.json": "attributes",
    }


# define these here because they exist outside the rev folder you're currently working in and fileio.path cant handle that
def path(target_value):
    if target_value == "library file":
        return os.path.join(dirpath("kicad"), f"{state.partnumber('pn')}.kicad_sym")
    return fileio.path(target_value)


def dirpath(target_value):
    if target_value == "kicad":
        return os.path.join(fileio.part_directory(), "kicad")
    return fileio.dirpath(target_value)


def generate_structure():
    os.makedirs(dirpath("kicad"), exist_ok=True)


def _make_new_library_file():
    """Create a bare .kicad_sym file with only library header info."""

    symbol_lib = [
        sexpdata.Symbol("kicad_symbol_lib"),
        [sexpdata.Symbol("version"), 20241209],
        [sexpdata.Symbol("generator"), "kicad_symbol_editor"],
        [sexpdata.Symbol("generator_version"), "9.0"],
    ]

    with open(path("library file"), "w", encoding="utf-8") as f:
        sexpdata.dump(symbol_lib, f, pretty=True)


def _parse_kicad_sym_file():
    """
    Load a KiCad .kicad_sym file and return its parsed sexp data.
    """
    with open(path("library file"), "r", encoding="utf-8") as f:
        data = sexpdata.load(f)
    return data


def _symbol_exists(kicad_library_data, target_symbol_name):
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


def _make_property(name, value, id_counter=None, hide=False):
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


def _add_blank_symbol(sym_name, value="", footprint="", datasheet="", description=""):
    """Append a blank symbol into the .kicad_sym at fileio.path('library file')."""

    lib_path = path("library file")

    # Load the existing s-expression
    with open(lib_path, "r", encoding="utf-8") as f:
        data = sexpdata.load(f)

    # Build symbol s-expression
    if rev_history.info(field="library_repo") in ["", None]:
        lib_repo_to_write = "local"
    else:
        lib_repo_to_write = _get_attribute("library_repo")
    symbol = [
        sexpdata.Symbol("symbol"),
        sym_name,
        [sexpdata.Symbol("exclude_from_sim"), sexpdata.Symbol("no")],
        [sexpdata.Symbol("in_bom"), sexpdata.Symbol("yes")],
        [sexpdata.Symbol("on_board"), sexpdata.Symbol("yes")],
        _make_property("Reference", _get_attribute("default_refdes")),
        _make_property("Value", value),
        _make_property("Footprint", footprint, hide=True),
        _make_property("Datasheet", datasheet, hide=True),
        _make_property("Description", _get_attribute("desc"), hide=True),
        _make_property("MFG", _get_attribute("manufacturer"), hide=False, id_counter=0),
        _make_property(
            "MPN", _get_attribute("manufacturer_part_number"), hide=False, id_counter=1
        ),
        _make_property("lib_repo", lib_repo_to_write, hide=True, id_counter=2),
        _make_property(
            "lib_subpath", _get_attribute("library_subpath"), hide=True, id_counter=3
        ),
        _make_property("rev", state.partnumber("rev"), hide=True, id_counter=4),
        [sexpdata.Symbol("embedded_fonts"), sexpdata.Symbol("no")],
    ]

    # Append to the library data
    data.append(symbol)

    # Write back out
    with open(lib_path, "w", encoding="utf-8") as f:
        sexpdata.dump(data, f, pretty=True)


def _overwrite_or_create_property_in_symbol(prop_name, value, hide=False):
    """
    Overwrite or create a property inside the target symbol block
    in the KiCad .kicad_sym library file.

    - File is always path("library file")
    - Symbol to modify is always named state.partnumber("pn-rev")

    Args:
        prop_name (str): Name of the property
        value (str): Value to set (will always be forced to string)
        hide (bool): Whether to hide the property
    """

    target_symbol_name = state.partnumber("pn-rev")

    # Ensure value is a string (KiCad requirement)
    if value is None:
        value = ""
    else:
        value = str(value)

    # Load the library file
    with open(path("library file"), "r", encoding="utf-8") as f:
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
        new_prop = _make_property(prop_name, value, id_counter=new_id, hide=hide)
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
    with open(path("library file"), "w", encoding="utf-8") as f:
        sexpdata.dump(data, f)


def _extract_pins_from_symbol(kicad_lib, symbol_name):
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


def _validate_pins(pins, unique_connectors_in_signals_list):
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


def _append_missing_pin(pin_name, pin_number, spacing=3.81):
    """
    Append a pin to the KiCad symbol whose name matches state.partnumber('pn-rev').
    Immediately writes the updated symbol back to path("library file").
    """
    file_path = path("library file")
    pin_number = str(pin_number)
    target_name = state.partnumber("pn-rev")

    import sexpdata

    # --- Load file ---
    with open(file_path, "r", encoding="utf-8") as f:
        symbol_data = sexpdata.load(f)

    # --- Find the symbol with matching name ---
    target_symbol = None
    for item in symbol_data:
        if (
            isinstance(item, list)
            and len(item) >= 2
            and isinstance(item[0], sexpdata.Symbol)
            and item[0].value() == "symbol"
        ):
            # (symbol "Name" ...)
            name_token = item[1]
            if isinstance(name_token, str) and name_token.strip() == target_name:
                target_symbol = item
                break

    if target_symbol is None:
        raise ValueError(f"No symbol named '{target_name}' found in {file_path}")

    # --- Skip if duplicate already present ---
    for elem in target_symbol[2:]:
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
                    and len(x) > 1
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
                    and len(x) > 1
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
                return symbol_data  # already present

    # --- Find max Y among existing pins ---
    max_y = -spacing
    for elem in target_symbol[2:]:
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
                    and len(x) >= 3
                    and isinstance(x[0], sexpdata.Symbol)
                    and x[0].value() == "at"
                ),
                None,
            )
            if at_entry:
                y_val = float(at_entry[2])
                max_y = max(max_y, y_val)

    new_y = max_y + spacing

    # --- Build new pin ---
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

    # --- Write back ---
    with open(file_path, "w", encoding="utf-8") as f:
        sexpdata.dump(symbol_data, f)

    print(
        f"Appended pin {pin_name} ({pin_number}) to symbol '{target_name}' in {os.path.basename(file_path)}"
    )
    return symbol_data


def _remove_details_from_signals_list():
    """Remove the specified channel-related columns from the signals list."""
    old_list = fileio.read_tsv("signals list")

    COLUMNS_TO_DROP = {"channel_id", "signal", "cavity"}

    new_list = []
    for row in old_list:
        filtered = {k: v for k, v in row.items() if k not in COLUMNS_TO_DROP}
        new_list.append(filtered)

    # Rewrite the TSV
    path = fileio.path("signals list")
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=signals_list.COLUMNS, delimiter="\t")
        writer.writeheader()
        writer.writerows(new_list)


def _next_free_number(seen_numbers, start=1):
    """Find the next unused pin number as a string."""
    n = start
    while True:
        if str(n) not in seen_numbers:
            return str(n)
        n += 1


def _validate_kicad_library():
    """
    Validate that the KiCad .kicad_sym library has:
    0. The .kicad_sym file exists (create if missing).
    1. A symbol matching the current part number.
    2. Pins that match the connectors in the signals list.
    """

    if not os.path.exists(path("library file")):
        _make_new_library_file()
        print("New Kicad symbol file created.")

    kicad_library_data = _parse_kicad_sym_file()

    if not _symbol_exists(kicad_library_data, state.partnumber("pn-rev")):
        _add_blank_symbol(
            sym_name=state.partnumber("pn-rev"),
        )

    # Step 1. Collect unique connectors from the signals list
    unique_connectors_in_signals_list = set()
    for signal in fileio.read_tsv("signals list"):
        connector_name = signal.get("connector_name")
        if connector_name:
            unique_connectors_in_signals_list.add(connector_name)

    # Step 2. Validate pins
    kicad_lib = _parse_kicad_sym_file()
    pins = _extract_pins_from_symbol(kicad_lib, state.partnumber("pn-rev"))
    missing, seen_numbers = _validate_pins(pins, unique_connectors_in_signals_list)

    kicad_library_data = _parse_kicad_sym_file()

    # Step 3. Append missing pins
    for pin_name in missing:
        # find the next available number
        pin_number = _next_free_number(seen_numbers)
        # append it
        _append_missing_pin(pin_name, pin_number)
        # mark number as used
        seen_numbers.add(pin_number)

    # Step 4. Overwrite symbol properties
    _overwrite_or_create_property_in_symbol(
        "Reference", _get_attribute("default_refdes"), hide=False
    )
    _overwrite_or_create_property_in_symbol(
        "Description", _get_attribute("desc"), hide=False
    )
    _overwrite_or_create_property_in_symbol("MFG", _get_attribute("mfg"), hide=True)
    _overwrite_or_create_property_in_symbol("MPN", _get_attribute("pn"), hide=False)

    if rev_history.info(field="library_repo") in ["", None]:
        _overwrite_or_create_property_in_symbol("lib_repo", "local", hide=True)
    else:
        _overwrite_or_create_property_in_symbol(
            "lib_repo", _get_attribute("library_repo"), hide=True
        )
    _overwrite_or_create_property_in_symbol(
        "lib_subpath", _get_attribute("library_subpath"), hide=True
    )
    _overwrite_or_create_property_in_symbol("rev", state.partnumber("rev"), hide=True)


def _validate_attributes_json():
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


def _get_attribute(attribute_key):
    # find an attribute from either revision history tsv or attributes json
    if attribute_key in rev_history.COLUMNS:
        return rev_history.info(field=attribute_key)

    else:
        with open(fileio.path("attributes"), "r", encoding="utf-8") as f:
            return json.load(f).get(attribute_key)


def configurations(sig_list):
    """
    Returns a dict of each configuration variable and each of its allowed options.
    {number} represents any number and can be used in a string like "{number}V".
    You can also say "0<={number}<10V" to describe bounds.

    Args:
    signals_list (dictionary form)

    Returns:
        {
            "config_col_1": {"opt1", "opt2", ""},
            "config_col_2": {"5V", "12V", ""},
            ...
        }
    """

    # collect headers
    headers = set()
    for item in sig_list:
        headers.update(item.keys())
        break  # only need first row for headers

    # find configuration columns
    configuration_cols = (
        headers - set(signals_list.DEVICE_COLUMNS) - {"config_variable"}
    )

    # initialize root dict
    configuration_vars = {col: set() for col in configuration_cols}

    # populate unique values (INCLUDING blanks)
    for row in sig_list:
        for col in configuration_cols:
            val = row.get(col)

            # normalize everything to string
            if val is None:
                val = ""
            else:
                val = str(val).strip()

            configuration_vars[col].add(val)

    return configuration_vars


def _validate_signals_list():
    print("--------------------------------")
    print("Validating signals list...")
    if not os.path.exists(fileio.path("signals list")):
        raise FileNotFoundError("Signals list was not generated.")

    with open(fileio.path("signals list"), "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        headers = reader.fieldnames
        signals_list = list(reader)

    if not headers:
        raise ValueError("Signals list has no header row.")

    #config_vars = configurations(signals_list)
    #print(json.dumps(config_vars, indent=4))
    # NEXT UP: WAIT UNTIL YOU HAVE A GOOD USE CASE OF CONFIGURED DEVICES.
    # CONFIRM THAT THIS PRINTS A DICTIONARY OF ALL THE VALID CONFIGURATION VARIABLES AND THEIR DEFINED STATES
    # THEN MAKE A LIST OF EVERY SINGLE FACTORIAL COMBINATION OF THE CONFIGURATION VARIABLES
    # THEN ITERATE THROUGH THAT LIST AND VALIDATE EACH CONFIGURATION

    counter = 2
    for signal in signals_list:
        print("Looking at csv row:", counter)

        found_signals = set()
        connector_names = set()

        # make sure all the fields are there
        if signal.get("channel_id") in ["", None]:
            raise ValueError("channel_id is blank")
        if signal.get("signal") in ["", None]:
            raise ValueError("signal is blank")
        if signal.get("connector_name") in ["", None]:
            raise ValueError("connector_name is blank")
        if signal.get("cavity") in ["", None]:
            raise ValueError("cavity is blank")
        if signal.get("connector_mpn") in ["", None]:
            raise ValueError("connector_mpn is blank")
        if signal.get("channel_type") in ["", None]:
            raise ValueError("channel_type is blank")
        
        # make sure channel type is formatted properly
        try:
            channel_type = chtype.parse(signal.get("channel_type"))
        except:
            raise TypeError("Channel type is not formatted correctly. See for more: https://harnice.io/products/_channel_type/")

        # collect expected signals of channel type
        expected_signals = chtype.signals(channel_type)

        # make sure signal is a valid signal of its channel type
        if signal.get("signal") not in chtype.signals(channel_type):
            raise ValueError(
                f"Signal {signal.get('signal')} is not a valid signal of its channel type"
            )

        # make sure all the signals of each channel type are present
        for expected_signal in expected_signals:
            for signal2 in signals_list:
                if (
                    signal2.get("channel_id") == signal.get("channel_id")
                    and signal2.get("signal") == expected_signal
                ):
                    found_signals.add(expected_signal)
                    connector_names.add(signal2.get("connector_name"))

        missing_signals = set(expected_signals) - found_signals
        if missing_signals:
            raise ValueError(
                f"Channel {signal.get('channel_id')} is missing signals: {', '.join(missing_signals)}"
            )

        # make sure no channels are spread across multiple connectors
        if len(connector_names) > 1:
            raise ValueError(
                f"Channel {signal.get('channel_id')} has signals spread across multiple connectors: "
                f"{', '.join(connector_names)}"
            )

        counter += 1

    # make sure no duplicate cavities are present
    seen_cavities = set()
    for signal in signals_list:
        cavity_key = f"{signal.get('connector_name')}-{signal.get('cavity')}"
        if cavity_key in seen_cavities:
            raise ValueError(
                f"Duplicate cavity '{signal.get('cavity')}' found on connector '{signal.get('connector_name')}'"
            )
        seen_cavities.add(cavity_key)

    print(f"Signals list of {state.partnumber('pn')} is valid.\n")


def render(lightweight=False):
    signals_list.set_list_type("device")
    _validate_attributes_json()

    # make a new signals list
    if not os.path.exists(fileio.path("signals list")):
        if lightweight:
            signals_list.new()
            signals_list.write_signal(
                connector_name="J1",
                channel_type=0,
                signal="placeholder",
                cavity=1,
                connector_mpn="DB9_F",
            )
        else:
            if not os.path.exists(fileio.path("feature tree")):
                with open(fileio.path("feature tree"), "w", encoding="utf-8") as f:
                    f.write(device_feature_tree_utils_default)

    if os.path.exists(fileio.path("feature tree")):
        runpy.run_path(fileio.path("feature tree"))
        print("Successfully rebuilt signals list per feature tree.")

    if not lightweight:
        _validate_signals_list()

    if lightweight:
        # don't want to map things that have not been mapped completely yet
        _remove_details_from_signals_list()

    path_nickname = ""
    subpath_nickname = ""
    if rev_history.info(field="library_repo"):
        path_nickname = f"{os.path.basename(rev_history.info(field='library_repo'))}/"
    if rev_history.info(field="library_subpath"):
        subpath_nickname = f"{rev_history.info(field='library_subpath')}"

    if path_nickname == "":
        print(
            "Add this to 'PROJECT SPECIFIC LIBRARIES' not 'global libraries' in Kicad because it doesn't look like you're working in a Harnice library path"
        )

    print(
        "\n"
        f"Nickname:       {path_nickname}{subpath_nickname}{state.partnumber('pn')}\n"
        f"Library path:   {path('library file')}\n"
    )

    _validate_kicad_library()
