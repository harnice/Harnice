import os
import runpy
import uuid as uuid_module
import xml.etree.ElementTree as ET
import json
import csv
from harnice import fileio, state
from harnice.lists import signals_list, rev_history
from harnice.products import chtype

default_desc = "DEVICE, FUNCTION, ATTRIBUTES, etc."

button_color = "#d376f5"

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
        f"{state.partnumber('pn-rev')}-block-diagram-symbol.svg": "block diagram symbol",
    }


def generate_structure():
    pass


def _ensure_svg_symbol_exists():
    """Create a minimal placeholder SVG if the symbol file does not exist."""
    path = fileio.path("block diagram symbol")
    if os.path.exists(path):
        return
    contents_id = f"{state.partnumber('pn-rev')}-contents-start"
    view_box = "0 0 400 400"
    root = ET.Element("svg", xmlns="http://www.w3.org/2000/svg", viewBox=view_box)
    root.set("data-bbox", view_box)
    ET.SubElement(
        root,
        "g",
        attrib={"id": contents_id, "class": "component device"},
    )
    ET.SubElement(
        root, "g", attrib={"id": f"{state.partnumber('pn-rev')}-contents-end"}
    )
    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ")
    with open(path, "wb") as f:
        tree.write(f, encoding="utf-8", default_namespace="", xml_declaration=True)
    return


def _validate_svg_symbol():
    """Ensure SVG symbol exists, has pins matching the signals list, and append any missing pins."""
    _ensure_svg_symbol_exists()
    path = fileio.path("block diagram symbol")
    tree = ET.parse(path)
    root = tree.getroot()

    def get_pin_name(elem):
        return (elem.get("data-pin-name") or "").strip()

    existing_pin_names = set()
    for elem in root.iter():
        if elem.tag.endswith("circle"):
            cls = (elem.get("class") or "").split()
            if "pin" in cls:
                name = get_pin_name(elem)
                if name:
                    existing_pin_names.add(name)

    unique_connectors_in_signals_list = set()
    for row in fileio.read_tsv("signals list"):
        cn = row.get("connector_name")
        if cn:
            unique_connectors_in_signals_list.add(cn)

    required = set(unique_connectors_in_signals_list)
    missing = required - existing_pin_names
    extra = existing_pin_names - required
    if extra:
        raise ValueError(
            f"The following pin(s) exist in SVG symbol but not in Signals List: {', '.join(sorted(extra))}"
        )

    if not missing:
        return

    def stable_pin_id(connector_name):
        seed = f"{state.partnumber('pn-rev')}-{connector_name}"
        return str(uuid_module.uuid5(uuid_module.NAMESPACE_DNS, seed))

    pin_spacing = 10

    def find_last_pin_y():
        last_y = 20
        for elem in root.iter():
            if (
                elem.tag.endswith("circle")
                and "pin" in (elem.get("class") or "").split()
            ):
                cy = elem.get("cy")
                if cy is not None:
                    try:
                        last_y = max(last_y, float(cy))
                    except ValueError:
                        pass
        return last_y

    next_y = find_last_pin_y() + pin_spacing
    contents_id = f"{state.partnumber('pn-rev')}-contents-start"
    insert_target = root.find(f".//*[@id='{contents_id}']")
    if insert_target is None:
        raise ValueError(
            f"Block diagram symbol SVG must contain a group with id '{contents_id}'"
        )

    for connector_name in sorted(missing):
        pin_id = stable_pin_id(connector_name)
        ET.SubElement(
            insert_target,
            "circle",
            attrib={
                "class": "pin",
                "data-pin-name": connector_name,
                "id": f"pin-{pin_id}",
                "cx": "50",
                "cy": str(next_y),
                "r": "4",
            },
        )
        next_y += pin_spacing

    ET.indent(tree, space="  ")
    with open(path, "wb") as f:
        tree.write(f, encoding="utf-8", default_namespace="", xml_declaration=True)


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

    # config_vars = configurations(signals_list)
    # print(json.dumps(config_vars, indent=4))
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
            raise TypeError(
                "Channel type is not formatted correctly. See for more: https://harnice.io/products/_channel_type/"
            )

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

    _validate_svg_symbol()
