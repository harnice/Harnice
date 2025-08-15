import os
import json
from harnice import fileio

def render():
    """
    Rebuild the master KiCad symbol library from all box JSONs in the repo.
    - If JSON exists but symbol doesn't → create it.
    - If symbol exists but JSON ports differ → raise error.
    - If symbol exists but JSON missing → delete it.
    Always writes a fully balanced .kicad_sym file from scratch.
    """

    # === Locate library output path ===
    boxes_dir = os.path.dirname(fileio.path("box definition json"))  # .../boxes
    container_dir = os.path.dirname(os.path.dirname(os.getcwd()))
    container_name = os.path.basename(container_dir)
    kicad_path = os.path.join(container_dir, "kicad", container_name + ".kicad_sym")
    os.makedirs(os.path.dirname(kicad_path), exist_ok=True)

    # === Collect JSON-defined boxes ===
    box_jsons = {}
    for root, _, files in os.walk(boxes_dir):
        for file in files:
            if file.endswith(".json"):
                json_path = os.path.join(root, file)
                with open(json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                part_name = os.path.splitext(file)[0]
                connectors = list(data.get("connectors", {}).keys())
                box_jsons[part_name] = connectors

    # === Parse existing library (if it exists) ===
    existing_symbols = {}
    if os.path.exists(kicad_path):
        with open(kicad_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        current_name = None
        current_body = []
        for line in lines:
            if line.strip().startswith('(symbol '):
                current_name = line.split('"')[1]
                current_body = [line.rstrip("\n")]
            elif current_name:
                current_body.append(line.rstrip("\n"))
                if line.strip() == ')':  # end of symbol
                    existing_symbols[current_name] = "\n".join(current_body)
                    current_name = None

    # === Decide which symbols to keep or add ===
    final_symbols = []

    for part_name, connectors in box_jsons.items():
        if part_name not in existing_symbols:
            # --- New symbol ---
            print(f"[ADD] Creating new symbol for {part_name}")
            pins = "\n".join(
                f'    (pin passive line (at -10 {i * 2.54} 0) (length 5)\n'
                f'      (name "{conn}" (effects (font (size 1.27 1.27))))\n'
                f'      (number "{i+1}" (effects (font (size 1.27 1.27))))\n'
                f'    )'
                for i, conn in enumerate(connectors)
            )
            new_symbol = f'  (symbol "{part_name}"\n{pins}\n  )'
            final_symbols.append(new_symbol)
        else:
            # --- Validate existing symbol ---
            ports_in_symbol = []
            for line in existing_symbols[part_name].splitlines():
                if line.strip().startswith('(name '):
                    ports_in_symbol.append(line.split('"')[1])
            if ports_in_symbol != connectors:
                raise ValueError(
                    f"[ERROR] Port mismatch in {part_name}:\n"
                    f"  JSON:   {connectors}\n"
                    f"  KiCad:  {ports_in_symbol}"
                )
            final_symbols.append(existing_symbols[part_name])

    # === Warn about orphans (symbols without JSON) ===
    for sym_name in existing_symbols:
        if sym_name not in box_jsons:
            print(f"[DEL] Removing orphan symbol {sym_name}")

    # === Write the library ===
    with open(kicad_path, "w", encoding="utf-8") as f:
        f.write('(kicad_symbol_lib (version 20211014) (generator "boxes-auto")\n')
        for sym in final_symbols:
            f.write(sym + "\n")
        f.write(')\n')

    print(f"[OK] Rebuilt {kicad_path} with {len(final_symbols)} symbols")