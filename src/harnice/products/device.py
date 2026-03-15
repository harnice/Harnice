import os
import re
import runpy
import tempfile
import uuid as uuid_module
import json
import csv
from pathlib import Path

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


def _atomic_write_svg(path_str, content_bytes: bytes):
    """Write SVG bytes atomically to avoid corruption from partial writes."""
    path = path_str if isinstance(path_str, str) else str(path_str)
    dirpath = os.path.dirname(path)
    if dirpath:
        os.makedirs(dirpath, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=dirpath or ".", suffix=".svg.tmp")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(content_bytes)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def _ensure_svg_symbol_exists():
    """Create a minimal placeholder SVG if the symbol file does not exist."""
    path = fileio.path("block diagram symbol")
    if os.path.exists(path):
        return
    contents_id = f"{state.partnumber('pn-rev')}-contents-start"
    contents_end = contents_id.replace("-contents-start", "-contents-end")
    view_box = "0 0 400 400"
    svg_text = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="{view_box}" data-bbox="{view_box}">
  <g id="{contents_id}" class="component device"></g>
  <g id="{contents_end}"></g>
</svg>
'''
    _atomic_write_svg(path, svg_text.encode("utf-8"))


def _validate_svg_symbol():
    """Ensure SVG symbol exists, has pins matching the signals list, and append any missing pins."""
    _ensure_svg_symbol_exists()
    path = fileio.path("block diagram symbol")
    svg_text = Path(path).read_text(encoding="utf-8")

    if "<svg" not in svg_text.lower() or "</svg>" not in svg_text.lower():
        os.remove(path)
        _ensure_svg_symbol_exists()
        svg_text = Path(path).read_text(encoding="utf-8")

    # Extract connector names from pin circles
    existing_pin_names = set()
    for m in re.finditer(r"<circle\s([^>]+)>", svg_text):
        attrs = m.group(1)
        class_match = re.search(r'class\s*=\s*["\']([^"\']*)["\']', attrs, re.I)
        if not class_match or "connector" not in class_match.group(1):
            continue
        name_match = re.search(r'data-pin-name\s*=\s*["\']([^"\']+)["\']', attrs, re.I)
        if name_match:
            existing_pin_names.add(name_match.group(1).strip())

    required = {
        row["connector_name"]
        for row in fileio.read_tsv("signals list")
        if row.get("connector_name")
    }
    missing = required - existing_pin_names
    extra = existing_pin_names - required
    if extra:
        raise ValueError(
            f"The following pin(s) exist in SVG symbol but not in Signals List: {', '.join(sorted(extra))}"
        )

    if not missing:
        return

    # Find max cy among pin circles (or 20 if none)
    last_y = 20.0
    for m in re.finditer(r"<circle\s([^>]+)>", svg_text):
        attrs = m.group(1)
        class_match = re.search(r'class\s*=\s*["\']([^"\']*)["\']', attrs, re.I)
        if not class_match or "connector" not in class_match.group(1):
            continue
        cy_match = re.search(r'cy\s*=\s*["\']?([\d.-]+)', attrs)
        if cy_match:
            try:
                last_y = max(last_y, float(cy_match.group(1)))
            except ValueError:
                pass

    contents_id = f"{state.partnumber('pn-rev')}-contents-start"
    next_y = last_y + 10
    pin_spacing = 10
    pin_lines = []
    for connector_name in sorted(missing):
        pin_id = str(
            uuid_module.uuid5(
                uuid_module.NAMESPACE_DNS,
                f"{state.partnumber('pn-rev')}-{connector_name}",
            )
        )
        cx, cy = 50, next_y
        pin_lines.append(
            f'  <circle class="connector" data-pin-name="{connector_name}" '
            f'id="pin-{pin_id}" cx="{cx}" cy="{cy}" r="0.1" fill="black" />'
        )
        next_y += pin_spacing

    # Insert pin elements immediately after the opening <g id="..."> of the contents-start group
    start_pattern = f'id="{contents_id}"'
    idx = svg_text.find(start_pattern)
    if idx == -1:
        raise ValueError(
            f'Block diagram symbol SVG must contain a group with id "{contents_id}"'
        )
    gt_pos = svg_text.find(">", idx)
    slash_gt = svg_text.find("/>", idx)
    pin_block = "\n  " + "\n    ".join(pin_lines) + "\n  "
    if slash_gt != -1 and slash_gt < gt_pos:
        close_slash = slash_gt
        updated = (
            svg_text[:close_slash]
            + ">\n  "
            + pin_block
            + "</g>"
            + svg_text[close_slash + 2 :]
        )
    else:
        insert_pos = gt_pos + 1
        updated = svg_text[:insert_pos] + pin_block + svg_text[insert_pos:]

    _atomic_write_svg(path, updated.encode("utf-8"))


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
