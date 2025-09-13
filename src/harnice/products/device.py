import os
import runpy
import csv
from harnice import fileio, icd
import sexpdata

signals_list_feature_tree_default = """
from harnice import icd

ch_type_ids = {
    "in": (1, "public"),
    "out": (4, "public"),
    "chassis": (5, "public")
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

icd.new_signals_list()

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

def validate_signals_list():
    if not os.path.exists(fileio.path("signals list")):
        raise FileNotFoundError("Signals list was not generated.")

    with open(fileio.path("signals list"), "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        headers = reader.fieldnames
        signals_list = list(reader)

    if not headers:
        raise ValueError("Signals list has no header row.")

    required_headers = icd.SIGNALS_HEADERS
    missing = [h for h in required_headers if h not in headers]
    if missing:
        raise ValueError(f"Signals list is missing headers: {', '.join(missing)}")

    if not signals_list:
        raise ValueError("Signals list has no data rows.")

    required_fields = [
        "channel",
        "signal",
        "connector_name",
        "channel_type_id",
        "compatible_channel_type_ids",
    ]

    for signal in signals_list:
        for field in required_fields:
            if field not in signal:
                raise ValueError(
                    f"Channel {signal.get('channel')} is missing the field: {field}"
                )

    for signal in signals_list:
        channel_type_id = signal.get("channel_type_id")
        expected_signals = icd.signals_of_channel_type_id(channel_type_id)
        found_signals = set()
        connector_names = set()

        for expected_signal in expected_signals:
            for signal2 in signals_list:
                if (
                    signal2.get("channel") == signal.get("channel")
                    and signal2.get("signal") == expected_signal
                ):
                    found_signals.add(expected_signal)
                    connector_names.add(signal2.get("connector_name"))

        missing_signals = set(expected_signals) - found_signals
        if missing_signals:
            raise ValueError(
                f"Channel {signal.get('channel')} is missing signals: {', '.join(missing_signals)}"
            )

        if len(connector_names) > 1:
            raise ValueError(
                f"Channel {signal.get('channel')} has signals spread across multiple connectors: "
                f"{', '.join(connector_names)}"
            )

    seen_contacts = set()
    for signal in signals_list:
        contact_key = f"{signal.get('connector_name')}-{signal.get('contact')}"
        if contact_key in seen_contacts:
            raise ValueError(f"Duplicate connector contact found: {contact_key}")
        seen_contacts.add(contact_key)

    print(f"Signals list of {fileio.partnumber('pn')} is valid.\n")

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

def parse_kicad_sym_file(file_path):
    """
    Load a KiCad .kicad_sym file and return its parsed sexp data.
    """
    with open(file_path, "r", encoding="utf-8") as f:
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

import sexpdata
from harnice import fileio

def add_blank_symbol(sym_name, default_refdes,
                     value="", footprint="", datasheet="", description=""):
    """Append a blank symbol into the .kicad_sym at fileio.path('library file')."""

    lib_path = fileio.path("library file")

    # Load the existing s-expression
    with open(lib_path, "r", encoding="utf-8") as f:
        data = sexpdata.load(f)

    def make_property(name, text, hide=False):
        prop = [
            sexpdata.Symbol("property"), name, text,
            [sexpdata.Symbol("at"), 0, 0, 0],
            [sexpdata.Symbol("effects"),
                [sexpdata.Symbol("font"),
                    [sexpdata.Symbol("size"), 1.27, 1.27]
                ]
            ]
        ]
        if hide:
            # add (hide yes) as symbols, not strings
            prop[-1].append([sexpdata.Symbol("hide"), sexpdata.Symbol("yes")])
        return prop

    # Build symbol s-expression
    symbol = [
        sexpdata.Symbol("symbol"), sym_name,
        [sexpdata.Symbol("exclude_from_sim"), sexpdata.Symbol("no")],
        [sexpdata.Symbol("in_bom"), sexpdata.Symbol("yes")],
        [sexpdata.Symbol("on_board"), sexpdata.Symbol("yes")],
        make_property("Reference", default_refdes),
        make_property("Value", value),
        make_property("Footprint", footprint, hide=True),
        make_property("Datasheet", datasheet, hide=True),
        make_property("Description", description, hide=True),
        [sexpdata.Symbol("embedded_fonts"), sexpdata.Symbol("no")]
    ]

    # Append to the library data
    data.append(symbol)

    # Write back out
    with open(lib_path, "w", encoding="utf-8") as f:
        sexpdata.dump(data, f, pretty=True)


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

    kicad_library_data = parse_kicad_sym_file(fileio.path("library file"))

    if not symbol_exists(kicad_library_data, fileio.partnumber("pn-rev")):
        add_blank_symbol(
            sym_name=fileio.partnumber("pn-rev"),
            default_refdes="U"
        )
    else:
        print(f"Symbol for {fileio.partnumber('pn-rev')} already exists")

    exit()
    # Step 1. Collect unique connectors from the signals list
    unique_connectors_in_signals_list = set()
    for signal in icd.read_signals_list():
        connector_name = signal.get("connector_name")
        if connector_name:
            unique_connectors_in_signals_list.add(connector_name)

    # Step 2. Load the KiCad library
    kicad_lib = parse_kicad_sym_file(sym_path)
    symbol_data = None

    # Step 3. Check if the symbol exists
    pn_rev = fileio.partnumber("pn-rev")
    for item in kicad_lib.get("kicad_symbol_lib", []):
        if "symbol" in item:
            data = item["symbol"]
            if isinstance(data, list) and data and data[0] == pn_rev:
                symbol_data = data
                break
    if symbol_data is None:
        raise ValueError(f"No symbol for {fileio.partnumber('R')} in library {fileio.partnumber('pn')}")

    # Step 4. Extract existing pins from the symbol
    existing_pins = set()
    for element in symbol_data:
        if isinstance(element, dict) and "pin" in element:
            pin_block = element["pin"]
            for entry in pin_block:
                if isinstance(entry, dict) and "name" in entry:
                    name = entry["name"][0] if isinstance(entry["name"], list) else entry["name"]
                    existing_pins.add(name)

    # Step 5. Check if pins exist for each connector
    counter = 1
    for connector in unique_connectors_in_signals_list:
        if connector not in existing_pins:
            raise ValueError(f"Missing pin in symbol for connector {connector}")
            counter += 1

    # Step 6. Verify no extra pins exist
    for pin in existing_pins:
        if pin not in unique_connectors_in_signals_list:
            raise ValueError(f"Pin {pin} exists in the symbol but not in the signals list.")

    print(f"Symbol for '{fileio.partnumber('pn-rev')}' has pins that match the connectors in the signals list.")

def device_render(lightweight=False):
    fileio.verify_revision_structure()
    fileio.generate_structure()

    if not lightweight:
        if not os.path.exists(fileio.path("signals list")):
            with open(fileio.path("feature tree"), "w", encoding="utf-8") as f:
                f.write(signals_list_feature_tree_default)
    else:
        if not os.path.exists(fileio.path("signals list")):
            icd.new_signals_list()
            icd.write_signal(connector_name="J1")

    if os.path.exists(fileio.path("feature tree")):
        runpy.run_path(fileio.path("feature tree"))
        print("Successfully rebuilt signals list per feature tree.")

    if not lightweight:
        validate_signals_list()

    validate_kicad_library()

def lightweight_render():
    device_render(lightweight=True)

def render():
    device_render(lightweight=False)
