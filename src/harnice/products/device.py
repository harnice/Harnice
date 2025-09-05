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

def generate_temp_symbol(symbol_name=None):
    """
    Use KiPart to generate a KiCad .kicad_sym part file from the kipart CSV.
    Always overwrites the temp symbol file.
    """
    csv_path = fileio.path("kipart csv")
    out_path = fileio.path("temp symbol")

    # Add -w so existing file is overwritten
    cmd = [
        "kipart",
        "-o", out_path,
        "-w",
        csv_path
    ]

    if symbol_name:
        cmd.extend(["-p", symbol_name])

    print("Running:", " ".join(cmd))
    subprocess.run(cmd, check=True)

    print(f"Temporary symbol written to {out_path}")
    return out_path


def build_kipart_csv():
    """
    Overwrites the kipart CSV in the 'spreadsheet' format KiPart expects:
    <part name>
    Pin,Type,Name
    1,unspecified,in1
    ...
    """
    signals_path = fileio.path("signals list")
    csv_path = fileio.path("kipart csv")

    # Derive part name from CWD (assumes PN-rev directory, e.g. SM58-rev2)
    cwd = os.getcwd()
    part_name = os.path.basename(cwd).split("-")[0]  # e.g. "SM58"

    connector_names = set()
    with open(signals_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")  # signals list is TSV
        for row in reader:
            connector_name = row.get("connector_name", "").strip()
            if connector_name:
                connector_names.add(connector_name)

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        # First line is the part name
        f.write(part_name + "\n")

        writer = csv.writer(f, delimiter=",")
        writer.writerow(["Pin", "Type", "Name"])
        for i, name in enumerate(sorted(connector_names), start=1):
            writer.writerow([i, "unspecified", name])

    print(f"KiPart CSV written to {csv_path} with {len(connector_names)} entries for part {part_name}.")
    return csv_path

def validate_signals_list():
    # make sure signals list exists
    if not os.path.exists(fileio.path("signals list")):
        raise FileNotFoundError("Signals list was not generated.")

    # load the signals list to read it in subsequent checks
    with open(fileio.path("signals list"), "r", encoding="utf-8") as f:
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

def s_exp_to_dict(exp):
    """Convert an S-expression parsed by sexpdata into Python dicts/lists."""
    if isinstance(exp, sexpdata.Symbol):
        return exp.value()
    elif isinstance(exp, list):
        if len(exp) > 0 and isinstance(exp[0], sexpdata.Symbol):
            head = exp[0].value()
            if len(exp) == 2:
                return {head: s_exp_to_dict(exp[1])}
            else:
                return {head: [s_exp_to_dict(e) for e in exp[1:]]}
        else:
            return [s_exp_to_dict(e) for e in exp]
    else:
        return exp  # numbers, strings, etc.

def parse_kicad_sym_file(file_path):
    """Parse a KiCad .kicad_sym file into a nested Python dict."""
    with open(file_path, "r", encoding="utf-8") as f:
        data = sexpdata.load(f)
    return s_exp_to_dict(data)

# Example usage:
# sym_dict = parse_kicad_sym_file(fileio.path("temp symbol"))
# print(json.dumps(sym_dict, indent=2))  # pretty-print as JSON if desired

def device_render(lightweight=False):
    fileio.verify_revision_structure()
    fileio.generate_structure()

    if not lightweight:
        # Create signals list feature tree file if no list.
        if not os.path.exists(fileio.path("signals list")):
            with open(fileio.path("feature tree"), "w", encoding="utf-8") as f:
                f.write(signals_list_feature_tree_default)

    # Run the signals list feature tree script
    if os.path.exists(fileio.path("feature tree")):
        runpy.run_path(fileio.path("feature tree"))
        print("Successfully rebuilt signals list per feature tree.")

    if not lightweight:
        validate_signals_list()

    build_kipart_csv()
    generate_temp_symbol()

def lightweight_render():
    device_render(lightweight=True)

def render():
    device_render(lightweight=False)
