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

def load_symbol(path, symbol_name):
    """Load a specific symbol S-expression from a .kicad_sym file."""
    with open(path, "r", encoding="utf-8") as f:
        tree = sexpdata.load(f)

    # .kicad_sym top-level: (kicad_symbol_lib (version ...) (generator ...) (symbol ...))
    for item in tree:
        if isinstance(item, list) and len(item) > 0 and item[0].value() == "symbol":
            if item[1].value() == symbol_name:
                return item
    raise ValueError(f"Symbol {symbol_name} not found in {path}")


def extract_pins(symbol):
    """Return dict {number: (pin_expr, name, type)} for easy comparison."""
    pins = {}
    for item in symbol:
        if isinstance(item, list) and item[0].value() == "pin":
            num = str(item[1].value())  # e.g. pin number
            name = str(item[2].value()) # pin name
            pins[num] = (item, name)
    return pins


def merge_symbols(existing_symbol, reference_symbol):
    """Update existing symbol pins to match reference, preserving coords/graphics."""
    existing_pins = extract_pins(existing_symbol)
    reference_pins = extract_pins(reference_symbol)

    updated = []
    # Keep existing non-pin elements (graphics, text, etc.)
    for item in existing_symbol:
        if not (isinstance(item, list) and item[0].value() == "pin"):
            updated.append(item)

    # Add updated pin list
    for num, (ref_pin, ref_name) in reference_pins.items():
        if num in existing_pins:
            old_pin, old_name = existing_pins[num]
            # Copy coordinates from old pin
            ref_pin = _merge_pin_coords(ref_pin, old_pin)
        updated.append(ref_pin)

    return ["symbol", existing_symbol[1]] + updated


def _merge_pin_coords(ref_pin, old_pin):
    """Replace the (at x y <orientation>) field in ref_pin with old_pin's."""
    def get_at(pin_expr):
        for el in pin_expr:
            if isinstance(el, list) and el[0].value() == "at":
                return el
        return None

    old_at = get_at(old_pin)
    if old_at:
        # Replace ref pin's "at" with old one
        for i, el in enumerate(ref_pin):
            if isinstance(el, list) and el[0].value() == "at":
                ref_pin[i] = old_at
    return ref_pin


def save_symbol(path, symbol, lib_meta=None):
    """Write back updated symbol into .kicad_sym (simplified)."""
    with open(path, "w", encoding="utf-8") as f:
        sexpdata.dump(["kicad_symbol_lib", symbol], f)

def validate_signals_list():
    # make sure signals list exists
    path = fileio.path("signals list")
    if not os.path.exists(path):
        raise FileNotFoundError("Signals list was not generated.")

    # load the signals list to read it in subsequent checks
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        headers = reader.fieldnames
        signals_list = list(reader)

    # --- Validate headers ---
    if not headers:
        raise ValueError("Signals list has no header row.")

    required_headers = icd.SIGNALS_HEADERS
    missing = [h for h in required_headers if h not in headers]
    if missing:
        raise ValueError(f"Signals list is missing headers: {', '.join(missing)}")

    # --- Validate data rows ---
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

    # --- Check every signal of a channel is accounted for ---
    for signal in signals_list:
        channel_type_id = signal.get("channel_type_id")
        expected_signals_of_channel = icd.signals_of_channel_type_id(channel_type_id)

        found_signals = set()
        connector_names = set()

        for expected_signal in expected_signals_of_channel:
            for signal2 in signals_list:
                if (
                    signal2.get("channel") == signal.get("channel")
                    and signal2.get("signal") == expected_signal
                ):
                    found_signals.add(expected_signal)
                    connector_names.add(signal2.get("connector_name"))

        # completeness
        missing_signals = set(expected_signals_of_channel) - found_signals
        if missing_signals:
            raise ValueError(
                f"Channel {signal.get('channel')} is missing signals: {', '.join(missing_signals)}"
            )

        # connector consistency
        if len(connector_names) > 1:
            raise ValueError(
                f"Channel {signal.get('channel')} has signals spread across multiple connectors: "
                f"{', '.join(connector_names)}"
            )

    # --- Check no duplicate connector contacts ---
    seen_contacts = set()
    for signal in signals_list:
        contact_key = f"{signal.get('connector_name')}-{signal.get('contact')}"
        if contact_key in seen_contacts:
            raise ValueError(f"Duplicate connector contact found: {contact_key}")
        seen_contacts.add(contact_key)

    print(f"Signals list of {fileio.partnumber('pn')} is valid.\n")

def update_symbol():
    # Load reference (from KiPart) and existing (user-edited)
    ref = load_symbol("reference.kicad_sym", "MyConnector")
    old = load_symbol("mylib.kicad_sym", "MyConnector")

    # Merge
    merged = merge_symbols(old, ref)

    # Save back to library
    save_symbol("mylib.kicad_sym", merged)

def device_render(lightweight=False):
    fileio.verify_revision_structure()

    if not lightweight:
        # Create signals list feature tree file if no list.
        if not os.path.exists(fileio.path("signals list")):
            with open(fileio.path("feature tree"), "w", encoding="utf-8") as f:
                f.write(signals_list_feature_tree_default)

        # Run the signals list feature tree script
        if os.path.exists(fileio.path("feature tree")):
            runpy.run_path(fileio.path("feature tree"))
            print("Successfully rebuilt signals list per feature tree.")

        validate_signals_list()

    if lightweight:
        icd.new_signals_list()

    update_symbol()

def lightweight_render():
    device_render(lightweight=True)

def render():
    device_render(lightweight=False)