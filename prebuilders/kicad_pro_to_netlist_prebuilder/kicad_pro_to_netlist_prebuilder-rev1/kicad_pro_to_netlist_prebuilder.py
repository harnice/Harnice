import os
import re
import json
from typing import Dict
from harnice import fileio

prebuilder_mpn = "kicad"

def path(target_value: str) -> str:
    if target_value == "kicad sch":
        return os.path.join(os.getcwd(), "kicad", f"{fileio.partnumber('pn-rev')}.kicad_sch")

    if target_value == "kicad pro":
        return os.path.join(os.getcwd(), "kicad", f"{fileio.partnumber('pn-rev')}.kicad_pro")

    if target_value == "netlist json":
        return f"{fileio.partnumber('pn-rev')}-netlist.json"

    raise KeyError(f"Filename {target_value} not found in {prebuilder_mpn} file tree")


def _parse_nets_from_text(export_text: str) -> Dict[str, Dict[str, str]]:
    """
    Simplified parser to extract nets from a KiCad export/pro file.
    """
    nets: Dict[str, Dict[str, str]] = {}
    for m in re.finditer(r'\(net\s+\(code\s+"[^"]*"\)\s+\(name\s+"([^"]+)"\)(.*?)\)', export_text, flags=re.S):
        net_name, body = m.groups()
        comp_map = {}
        for node in re.finditer(r'\(node\s+\(ref\s+"([^"]+)"\).*?\(pinfunction\s+"([^"]*)"', body):
            ref, pinfunc = node.groups()
            comp_map[ref] = pinfunc
        nets[net_name] = comp_map
    return nets


# === Inline execution ===

text = ""
for candidate in [path("kicad pro"), path("kicad sch")]:
    if os.path.exists(candidate):
        with open(candidate, "r", encoding="utf-8") as f:
            text = f.read()
        break

if not text:
    raise FileNotFoundError("Neither .kicad_pro nor .kicad_sch project file found")

nets = _parse_nets_from_text(text)

# Save JSON to the defined netlist path
outpath = path("netlist json")
with open(outpath, "w", encoding="utf-8") as f:
    json.dump(nets, f, indent=2)

print(f"Netlist JSON written to {outpath}")
