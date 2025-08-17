import os
import re
import json
import subprocess
from typing import Dict
from harnice import fileio

prebuilder_mpn = "kicad"

def path(target_value: str) -> str:
    if target_value == "kicad sch":
        return os.path.join(os.getcwd(), "kicad", f"{fileio.partnumber('pn-rev')}.kicad_sch")

    if target_value == "kicad pro":
        return os.path.join(os.getcwd(), "kicad", f"{fileio.partnumber('pn-rev')}.kicad_pro")

    if target_value == "netlist source":
        return os.path.join(os.getcwd(), "kicad", f"{fileio.partnumber('pn-rev')}.net")

    if target_value == "netlist json":
        return f"{fileio.partnumber('pn-rev')}-netlist.json"

    if target_value == "bom json":
        return f"{fileio.partnumber('pn-rev')}-bom.json"

    if target_value == "netclasses json":
        return f"{fileio.partnumber('pn-rev')}-netclasses.json"

    raise KeyError(f"Filename {target_value} not found in {prebuilder_mpn} file tree")

def parse_nets_from_export(export_text: str) -> Dict[str, list[str]]:
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
                refname = ref.group(1)
                func = pinfunc.group(1)
                nets[current_net].append(f"{refname}:{func}")

        # End of net
        elif line == ")" and current_net:
            current_net = None

    return nets


def parse_bom_from_sch(sch_text: str) -> Dict[str, Dict[str, str]]:
    bom: Dict[str, Dict[str, str]] = {}
    for comp in re.finditer(
        r'\(comp\s+\(ref\s+"([^"]+)"\).*?\(libsource\s+\(lib\s+"([^"]+)"\)\s+\(part\s+"([^"]+)"\)',
        sch_text,
        flags=re.S,
    ):
        ref, lib, part = comp.groups()
        bom[ref] = {"lib": lib, "part": part}
    return bom


def parse_netclasses_from_pro(pro_text: str):
    data = json.loads(pro_text)
    return data.get("net_settings", {}).get("classes", [])


def export_netlist_if_missing():
    """
    Ensure .net file exists using KiCad CLI.
    """
    net_file = path("netlist source")
    sch_file = path("kicad sch")

    if os.path.exists(net_file):
        return net_file

    if not os.path.exists(sch_file):
        raise FileNotFoundError("No schematic file (.kicad_sch) found")

    try:
        subprocess.run(
            ["kicad-cli", "sch", "export", "netlist", sch_file, "--output", net_file],
            check=True
        )
        print(f"Exported netlist using kicad-cli → {net_file}")
        return net_file
    except FileNotFoundError:
        raise RuntimeError(
            "kicad-cli not found on PATH.\n\n"
            "To install KiCad CLI:\n"
            "  • macOS (Homebrew):\n"
            "      brew install --cask kicad\n"
            "      export PATH=\"/Applications/KiCad/KiCad.app/Contents/MacOS:$PATH\"\n\n"
            "  • Ubuntu/Debian:\n"
            "      sudo apt install kicad\n\n"
            "  • Fedora:\n"
            "      sudo dnf install kicad\n\n"
            "  • Windows:\n"
            "      Install KiCad 7 or 8 from https://kicad.org/download/\n"
            "      Then add C:\\Program Files\\KiCad\\bin to your PATH.\n\n"
            "After installation, verify with:\n"
            "      kicad-cli --version\n"
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"kicad-cli export failed: {e}")


# === Inline execution ===

net_file = export_netlist_if_missing()

with open(net_file, "r", encoding="utf-8") as f:
    net_text = f.read()
nets = parse_nets_from_export(net_text)

sch_file = path("kicad sch")
with open(sch_file, "r", encoding="utf-8") as f:
    sch_text = f.read()
bom = parse_bom_from_sch(sch_text)

pro_file = path("kicad pro")
with open(pro_file, "r", encoding="utf-8") as f:
    pro_text = f.read()
netclasses = parse_netclasses_from_pro(pro_text)

with open(path("netlist json"), "w", encoding="utf-8") as f:
    json.dump(nets, f, indent=2)

with open(path("bom json"), "w", encoding="utf-8") as f:
    json.dump(bom, f, indent=2)

with open(path("netclasses json"), "w", encoding="utf-8") as f:
    json.dump(netclasses, f, indent=2)

print(f"Netlist JSON written to {path('netlist json')}")
print(f"BOM JSON written to {path('bom json')}")
print(f"Netclasses JSON written to {path('netclasses json')}")
