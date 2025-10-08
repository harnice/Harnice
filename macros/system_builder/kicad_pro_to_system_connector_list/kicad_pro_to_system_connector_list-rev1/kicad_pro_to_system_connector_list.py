import os
import re
import shutil
import subprocess
import csv
from typing import Dict
from harnice import fileio

build_macro_mpn = "kicad_pro_to_system_connector_list"


def path(target_value: str) -> str:
    if target_value == "kicad sch":
        return os.path.join(
            os.getcwd(), "kicad", f"{fileio.partnumber('pn-rev')}.kicad_sch"
        )

    if target_value == "netlist source":
        return os.path.join(os.getcwd(), "kicad", f"{fileio.partnumber('pn-rev')}.net")

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


def merge_disconnect_nets(
    nets: Dict[str, list[str]], disconnect_refdes: set[str]
) -> Dict[str, list[tuple[str, str]]]:
    """
    Merge nets connected through any chain of disconnects.
    Returns {merged_net: [(conn_string, orig_net), ...]}.
    """

    # Build adjacency map of nets <-> nets via disconnect refdes
    adjacency: Dict[str, set[str]] = {k: set() for k in nets}
    for refdes in disconnect_refdes:
        involved_keys = [
            k for k, conns in nets.items() if any(refdes in c for c in conns)
        ]
        for i in range(len(involved_keys)):
            for j in range(i + 1, len(involved_keys)):
                a, b = involved_keys[i], involved_keys[j]
                adjacency[a].add(b)
                adjacency[b].add(a)

    # DFS to find connected components of nets
    visited = set()
    groups: list[set[str]] = []

    for net in nets:
        if net not in visited:
            stack = [net]
            group = set()
            while stack:
                cur = stack.pop()
                if cur in visited:
                    continue
                visited.add(cur)
                group.add(cur)
                stack.extend(adjacency[cur])
            groups.append(group)

    # Build merged net dictionary
    merged: Dict[str, list[tuple[str, str]]] = {}
    for group in groups:
        if len(group) == 1:
            net = next(iter(group))
            merged[net] = [(c, net) for c in nets[net]]
        else:
            new_key = "+".join(sorted(group))
            conns: list[tuple[str, str]] = []
            for net in group:
                for c in nets[net]:
                    conns.append((c, net))
            merged[new_key] = conns

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
merged_nets = merge_disconnect_nets(nets, disconnect_refdes)

# write contents to TSV
with open(fileio.path("system connector list"), "w", newline="", encoding="utf-8") as f:
    fieldnames = ["device_refdes", "connector", "net", "merged_net", "disconnect", "connector_mpn"]
    writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")
    writer.writeheader()

    for merged_net, conns in merged_nets.items():
        for conn, orig_net in conns:
            device_refdes, pinfunction = conn, ""
            if ":" in conn:
                device_refdes, pinfunction = conn.split(":", 1)

            disconnect_flag = "TRUE" if device_refdes in disconnect_refdes else ""

            # figure out connector mpn
            connector_mpn = ""
            if disconnect_flag:
                path_to_signals_list = os.path.join(os.getcwd(), "disconnects", device_refdes, f"{device_refdes}-signals_list.tsv")
            else:
                path_to_signals_list = os.path.join(os.getcwd(), "devices", device_refdes, f"{device_refdes}-signals_list.tsv")
            with open(path_to_signals_list, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f, delimiter="\t")
                for row in reader:
                    if row.get("connector_name", "").strip() == pinfunction.strip():
                        connector_mpn = row.get("connector_mpn", "").strip()
                        break

            writer.writerow(
                {
                    "device_refdes": device_refdes,
                    "connector": pinfunction,
                    "net": orig_net,  # original net
                    "merged_net": merged_net,  # merged net
                    "disconnect": disconnect_flag,
                    "connector_mpn": connector_mpn,
                }
            )
