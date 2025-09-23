import os
import re
import json
import shutil
import subprocess
import csv
from typing import Dict
from harnice import fileio

build_macro_mpn = "kicad_pro_to_netlist"


def path(target_value: str) -> str:
    if target_value == "kicad sch":
        return os.path.join(
            os.getcwd(), "kicad", f"{fileio.partnumber('pn-rev')}.kicad_sch"
        )

    if target_value == "netlist source":
        return os.path.join(os.getcwd(), "kicad", f"{fileio.partnumber('pn-rev')}.net")

    if target_value == "netlist json":
        return f"{fileio.partnumber('pn-rev')}-netlist.json"

    raise KeyError(f"Filename {target_value} not found in {build_macro_mpn} file tree")


def parse_nets_from_export(export_text: str) -> Dict[str, list[str]]:
    """
    Parse S-expression netlist (.net) into a dict {net_name: [ref:pinfunction, ...]}.
    """
    nets: Dict[str, list[str]] = {}
    current_net = None

    for line in export_text.splitlines():
        line = line.strip()

        # Start of a net
        if line.startswith("(net "):
            m = re.search(r'\(name\s+"([^"]+)"\)', line)
            if m:
                current_net = m.group(1)
                nets[current_net] = []

        # Node lines
        elif current_net and line.startswith("(node "):
            ref = re.search(r'\(ref\s+"([^"]+)"\)', line)
            pinfunc = re.search(r'\(pinfunction\s+"([^"]*)"\)', line)
            if ref and pinfunc:
                nets[current_net].append(f"{ref.group(1)}:{pinfunc.group(1)}")

        # End of net block
        elif line == ")" and current_net:
            current_net = None

    return nets


def export_netlist():
    """
    Always export schematic netlist in S-expression format, overwriting if it exists.
    Returns the path to the generated netlist file.
    """
    net_file = path("netlist source")
    sch_file = path("kicad sch")

    if not os.path.exists(sch_file):
        raise FileNotFoundError("No schematic file (.kicad_sch) found")

    # Try PATH first, then macOS app bundle fallback
    kicad_cli = shutil.which("kicad-cli")
    if not kicad_cli:
        fallback = "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"
        if os.path.exists(fallback):
            kicad_cli = fallback
        else:
            raise RuntimeError(
                "kicad-cli not found (neither on PATH nor in /Applications/KiCad)"
            )

    try:
        subprocess.run(
            [kicad_cli, "sch", "export", "netlist", sch_file, "--output", net_file],
            check=True,
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"kicad-cli export failed: {e}")

    return net_file


def find_disconnects() -> set[str]:
    """Read BOM TSV and return set of refdes marked as disconnect=True."""
    disconnects = set()
    with open(fileio.path("bom"), newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            if str(row.get("disconnect", "")).strip().lower() == "true":
                disconnects.add(row["device_ref_des"])
    return disconnects


def merge_disconnect_nets(nets: Dict[str, list[str]], disconnect_refdes: set[str]) -> Dict[str, list[str]]:
    """
    Merge nets that are connected through 2-port disconnect devices.
    Collapse ports into just the refdes (e.g. X1 instead of X1:A, X1:B).
    """
    merged = {}
    skip_keys = set()

    # Look for pairs of nets sharing each disconnect
    for refdes in disconnect_refdes:
        involved_keys = [k for k, conns in nets.items() if any(refdes in c for c in conns)]
        if len(involved_keys) == 2:
            k1, k2 = involved_keys
            new_key = f"{k1}+{k2}"
            merged_conns = []

            for k in [k1, k2]:
                for c in nets[k]:
                    if refdes in c:
                        if refdes not in merged_conns:
                            merged_conns.append(refdes)
                    else:
                        merged_conns.append(c)

            merged[new_key] = merged_conns
            skip_keys.update(involved_keys)

    # Keep all others unchanged
    for k, v in nets.items():
        if k not in skip_keys:
            merged[k] = v

    return merged


# -------------------------------
# Main workflow
# -------------------------------
net_file = export_netlist()

with open(net_file, "r", encoding="utf-8") as f:
    net_text = f.read()
nets = parse_nets_from_export(net_text)

# merge nets connected by disconnects
disconnect_refdes = find_disconnects()
nets = merge_disconnect_nets(nets, disconnect_refdes)

# write contents to json
with open(path("netlist json"), "w", encoding="utf-8") as f:
    json.dump(nets, f, indent=2)
