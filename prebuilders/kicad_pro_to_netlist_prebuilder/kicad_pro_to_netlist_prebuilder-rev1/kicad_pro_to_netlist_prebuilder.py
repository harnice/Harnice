import os
import re
import json
import shutil
import subprocess
from typing import Dict
from harnice import fileio

prebuilder_mpn = "kicad_pro_to_netlist"

def path(target_value: str) -> str:
    if target_value == "kicad sch":
        return os.path.join(os.getcwd(), "kicad", f"{fileio.partnumber('pn-rev')}.kicad_sch")

    if target_value == "netlist source":
        return os.path.join(os.getcwd(), "kicad", f"{fileio.partnumber('pn-rev')}.net")

    if target_value == "netlist json":
        return f"{fileio.partnumber('pn-rev')}-netlist.json"

    raise KeyError(f"Filename {target_value} not found in {prebuilder_mpn} file tree")


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
            raise RuntimeError("kicad-cli not found (neither on PATH nor in /Applications/KiCad)")

    try:
        subprocess.run(
            [
                kicad_cli, "sch", "export", "netlist",
                sch_file,
                "--output", net_file
            ],
            check=True
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"kicad-cli export failed: {e}")

    return net_file



# === Inline execution ===

net_file = export_netlist()

with open(net_file, "r", encoding="utf-8") as f:
    net_text = f.read()
nets = parse_nets_from_export(net_text)

with open(path("netlist json"), "w", encoding="utf-8") as f:
    json.dump(nets, f, indent=2)
