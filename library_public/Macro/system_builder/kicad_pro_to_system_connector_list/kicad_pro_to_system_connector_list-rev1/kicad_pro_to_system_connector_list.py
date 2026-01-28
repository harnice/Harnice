import os
import re
import shutil
import subprocess
import csv
from typing import Dict
from harnice import fileio, state

build_macro_mpn = "kicad_pro_to_system_connector_list"


def file_structure():
    return {
        "kicad": {
            f"{state.partnumber('pn-rev')}.kicad_sch": "kicad sch",
            f"{state.partnumber('pn-rev')}.net": "netlist source",
        }
    }


def parse_nets_from_export(export_text: str) -> Dict[str, list[str]]:
    """
    Parse KiCad S-expression netlist (.net) into a dict:
        {net_name: [ref:pinfunction, ...]}
    """
    nets: Dict[str, list[str]] = {}
    current_net = None

    for line in export_text.splitlines():
        line = line.strip()

        if line.startswith("(net "):
            m = re.search(r'\(name\s+"([^"]+)"\)', line)
            if m:
                current_net = m.group(1)
                nets[current_net] = []

        elif current_net and line.startswith("(node "):
            ref = re.search(r'\(ref\s+"([^"]+)"\)', line)
            pinfunc = re.search(r'\(pinfunction\s+"([^"]*)"\)', line)
            if ref and pinfunc:
                nets[current_net].append(f"{ref.group(1)}:{pinfunc.group(1)}")

        elif line == ")" and current_net:
            current_net = None

    return nets


def export_netlist() -> str:
    """Export schematic netlist (.net) via KiCad CLI."""
    net_file = fileio.path("netlist source", structure_dict=file_structure())
    sch_file = fileio.path("kicad sch", structure_dict=file_structure())

    if not os.path.exists(sch_file):
        raise FileNotFoundError("No schematic file (.kicad_sch) found")

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
        proc = subprocess.run(
            [kicad_cli, "sch", "export", "netlist", sch_file, "--output", net_file],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        if proc.returncode != 0:
            raise RuntimeError(proc.stderr.strip())
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"kicad-cli export failed: {e}")

    return net_file


def find_disconnects() -> set[str]:
    """Read BOM TSV and return set of device refdes where disconnect=True."""
    disconnects = set()
    with open(fileio.path("bom"), newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            if str(row.get("disconnect", "")).strip().lower() not in ["", None]:
                disconnects.add(row.get("device_refdes", "").strip())
    return disconnects


def merge_disconnect_nets(
    nets: Dict[str, list[str]], disconnect_refdes: set[str]
) -> Dict[str, list[tuple[str, str]]]:
    """
    Merge nets connected through any chain of disconnects.
    Returns {merged_net: [(conn_string, orig_net), ...]}.
    """
    adjacency: Dict[str, set[str]] = {k: set() for k in nets}

    for refdes in disconnect_refdes:
        involved = [k for k, conns in nets.items() if any(refdes in c for c in conns)]
        for i in range(len(involved)):
            for j in range(i + 1, len(involved)):
                a, b = involved[i], involved[j]
                adjacency[a].add(b)
                adjacency[b].add(a)

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

    merged: Dict[str, list[tuple[str, str]]] = {}
    for group in groups:
        merged_key = "+".join(sorted(group)) if len(group) > 1 else next(iter(group))
        merged[merged_key] = [(c, net) for net in group for c in nets[net]]

    return merged


def main():
    net_file = export_netlist()

    with open(net_file, "r", encoding="utf-8") as f:
        nets = parse_nets_from_export(f.read())

    disconnect_refdes = find_disconnects()
    merged_nets = merge_disconnect_nets(nets, disconnect_refdes)

    output_path = fileio.path("system connector list")
    fieldnames = [
        "device_refdes",
        "connector",
        "net",
        "merged_net",
        "disconnect",
        "connector_mpn",
    ]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()

        for merged_net, conns in merged_nets.items():
            for conn, orig_net in conns:
                device_refdes, pinfunction = (conn.split(":", 1) + [""])[:2]
                disconnect_flag = "TRUE" if device_refdes in disconnect_refdes else ""
                connector_mpn = ""

                # Decide directory based on disconnect flag
                base_dir = os.path.join(
                    fileio.dirpath("instance_data"),
                    ("disconnect" if disconnect_flag else "device"),
                )
                signals_list_path = os.path.join(
                    os.getcwd(),
                    base_dir,
                    device_refdes,
                    f"{device_refdes}-signals_list.tsv",
                )

                with open(signals_list_path, newline="", encoding="utf-8") as sigfile:
                    reader = csv.DictReader(sigfile, delimiter="\t")
                    for row in reader:
                        if disconnect_flag:
                            if pinfunction == "A":
                                connector_mpn = row.get("B_connector_mpn", "")
                            elif pinfunction == "B":
                                connector_mpn = row.get("A_connector_mpn", "")
                            break
                        else:
                            if (
                                row.get("connector_name", "").strip()
                                == pinfunction.strip()
                            ):
                                connector_mpn = row.get("connector_mpn", "").strip()
                                break

                writer.writerow(
                    {
                        "device_refdes": device_refdes,
                        "connector": pinfunction,
                        "net": orig_net,
                        "merged_net": merged_net,
                        "disconnect": disconnect_flag,
                        "connector_mpn": connector_mpn,
                    }
                )


if __name__ == "__main__":
    main()
