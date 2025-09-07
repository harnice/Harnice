import os
import runpy
import csv
from harnice import fileio, icd
import subprocess
import sexpdata
import json

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

def s_exp_to_dict(sexp):
    if isinstance(sexp, list):
        if sexp and isinstance(sexp[0], sexpdata.Symbol):
            key = sexp[0].value()
            return {key: [s_exp_to_dict(x) for x in sexp[1:]]}
        else:
            return [s_exp_to_dict(x) for x in sexp]
    elif isinstance(sexp, sexpdata.Quoted):
        return sexp.value()
    elif isinstance(sexp, sexpdata.Symbol):
        return sexp.value()
    else:
        return sexp

def dict_to_s_exp(obj):
    if isinstance(obj, dict):
        s_exp = []
        for key, value in obj.items():
            s_exp.append(sexpdata.Symbol(key))
            if isinstance(value, list):
                if all(not isinstance(v, (dict, list)) for v in value):
                    for v in value:
                        s_exp.append(dict_to_s_exp(v))
                else:
                    for v in value:
                        s_exp.append(dict_to_s_exp(v))
            else:
                s_exp.append(dict_to_s_exp(value))
        return s_exp

    elif isinstance(obj, list):
        return [dict_to_s_exp(x) for x in obj]

    elif isinstance(obj, str):
        if obj.lower() in ("yes", "no"):
            return sexpdata.Symbol(obj.lower())
        return obj

    elif isinstance(obj, sexpdata.Symbol):
        return obj

    else:
        return obj

def write_kicad_sym_file(file_path, data):
    print(data)
    sexp = dict_to_s_exp(data)
    with open(file_path, "w", encoding="utf-8") as f:
        sexpdata.dump(sexp, f)

def make_effects(hide=False):
    """
    Return a KiCad-correct effects block:
    (effects
      (font (size 1.27 1.27))
      (hide yes)  ; if hide=True
    )
    """
    effects = []
    effects.append({"font": [{"size": [1.27, 1.27]}]})
    if hide:
        effects.append({"hide": sexpdata.Symbol("yes")})
    return {"effects": effects}

def add_blank_symbol(pn_rev=None):
    sym_path = fileio.path("real symbol")
    kicad_lib = parse_kicad_sym_file(sym_path)

    if pn_rev is None:
        pn_rev = fileio.partnumber("pn-rev")

    def make_property(name, value, hide=False):
        return {
            "property": [
                name,
                value,
                {"at": [0, 0, 0]},
                make_effects(hide=hide)
            ]
        }

    new_symbol = {
        "symbol": [
            pn_rev,
            {"exclude_from_sim": sexpdata.Symbol("no")},
            {"in_bom": sexpdata.Symbol("yes")},
            {"on_board": sexpdata.Symbol("yes")},
            make_property("Reference", "U"),
            make_property("Value", ""),
            make_property("Footprint", "", hide=True),
            make_property("Datasheet", "", hide=True),
            make_property("Description", "", hide=True),
        ]
    }

    kicad_lib["kicad_symbol_lib"].append(new_symbol)

    with open(sym_path, "w", encoding="utf-8") as f:
        sexpdata.dump(dict_to_s_exp(kicad_lib), f)

    print(f"Blank symbol '{pn_rev}' added to {sym_path}")

def add_pin(pin_info):
    sym_path = fileio.path("real symbol")
    kicad_lib = parse_kicad_sym_file(sym_path)
    pn_rev = fileio.partnumber("pn-rev")

    symbol_data = None
    for item in kicad_lib.get("kicad_symbol_lib", []):
        if "symbol" in item:
            data = item["symbol"]
            if isinstance(data, list) and data and data[0] == pn_rev:
                symbol_data = data
                break
    if symbol_data is None:
        raise ValueError(f"Symbol {pn_rev} not found in {sym_path}")

    new_pin = {
        "pin": [
            "passive",
            "line",
            {"at": [0, 0, "right"]},
            {"length": 200},
            {"name": [
                pin_info["name"],
                make_effects()
            ]},
            {"number": [
                str(pin_info["number"]),
                make_effects()
            ]}
        ]
    }

    symbol_data.append(new_pin)

    with open(sym_path, "w", encoding="utf-8") as f:
        sexpdata.dump(dict_to_s_exp(kicad_lib), f)

    print(f"Added pin '{pin_info['name']}' (#{pin_info['number']}) to {pn_rev}")

def remove_pin(pin):
    raise NotImplementedError(
        f"Please remove a pin from the symbol in KiCad (called '{fileio.partnumber('pn-rev')}')."
    )

def parse_kicad_sym_file(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        data = sexpdata.load(f)
    return s_exp_to_dict(data)

def validate_kicad_library():
    """
    Validate that the KiCad .kicad_sym library has:
    0. The .kicad_sym file exists (create if missing).
    1. A symbol matching the current part number.
    2. Pins that match the connectors in the signals list.
    """

    sym_path = fileio.path("real symbol")
    if not os.path.exists(sym_path):
        print(f"[DEBUG] Symbol file missing, creating new: {sym_path}")
        blank_lib = {"kicad_symbol_lib": [
            {"version": 20211014},
            {"generator": "harnice"}
        ]}
        with open(sym_path, "w", encoding="utf-8") as f:
            sexpdata.dump(dict_to_s_exp(blank_lib), f)

    # Step 1. Collect unique connectors from the signals list
    unique_connectors_in_signals_list = set()
    for signal in icd.read_signals_list():
        connector_name = signal.get("connector_name")
        if connector_name:
            unique_connectors_in_signals_list.add(connector_name)

    print(f"[DEBUG] Connectors found in signals list: {unique_connectors_in_signals_list}")

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
        print(f"[DEBUG] No symbol for {pn_rev}, creating blank one")
        add_blank_symbol(pn_rev)
        return

    print(f"[DEBUG] Found symbol for {pn_rev}")

    # Step 4. Extract existing pins from the symbol
    existing_pins = set()
    for element in symbol_data:
        if isinstance(element, dict) and "pin" in element:
            pin_block = element["pin"]
            for entry in pin_block:
                if isinstance(entry, dict) and "name" in entry:
                    name = entry["name"][0] if isinstance(entry["name"], list) else entry["name"]
                    existing_pins.add(name)

    print(f"[DEBUG] Existing pins in symbol: {existing_pins}")

    # Step 5. Check if pins exist for each connector
    counter = 1
    for connector in unique_connectors_in_signals_list:
        if connector not in existing_pins:
            print(f"[DEBUG] Adding pin for connector {connector} as #{counter}")
            add_pin({
                "name": connector,
                "number": str(counter),
            })
            counter += 1

    # Step 6. Verify no extra pins exist
    for pin in existing_pins:
        if pin not in unique_connectors_in_signals_list:
            raise ValueError(f"Pin {pin} exists in the symbol but not in the signals list.")

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
