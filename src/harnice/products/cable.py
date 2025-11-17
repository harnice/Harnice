import os
import csv
import json
from harnice import fileio, state


default_desc = "CABLE, FUNCTION, ATTRIBUTES, etc."


def file_structure():
    return {
        f"{state.partnumber('pn-rev')}-attributes.json": "attributes",
        f"{state.partnumber('pn-rev')}-conductor_list.tsv": "conductor list",
    }


def generate_structure():
    pass


def render():
    # ========== Default JSON ==========
    default_attributes = {
        "jacket": {
            "properties": {
                "color": "gray",
                "material": "pvc",
                "od": "0.204in",
                "thickness": "0.028in",
            },
            "shield": {
                "properties": {"type": "foil", "coverage": "100%"},
                "drain_wire": {
                    "conductor": True,
                    "properties": {"gauge": "20AWG", "construction": "7x28"},
                    "appearance": {
                        "outline_color": "gray",
                        "slash_lines": {"direction": "RH", "color": "gray"},
                    },
                },
                "pair_1": {
                    "properties": {"twists": "12 per inch"},
                    "black": {
                        "conductor": True,
                        "properties": {
                            "insulation material": "polyethylene",
                            "od": "0.017in",
                            "gauge": "20AWG",
                            "construction": "7x28",
                            "material": "copper",
                        },
                        "appearance": {"base_color": "black"},
                    },
                    "white": {
                        "conductor": True,
                        "properties": {
                            "insulation material": "polyethylene",
                            "od": "0.017in",
                            "gauge": "20AWG",
                            "construction": "7x28",
                            "material": "copper",
                        },
                        "appearance": {"base_color": "white", "outline_color": "black"},
                    },
                },
            },
        }
    }

    attributes_path = fileio.path("attributes")

    # ========== Load or create attributes.json ==========
    if os.path.exists(attributes_path):
        try:
            with open(attributes_path, "r", encoding="utf-8") as f:
                attrs = json.load(f)
        except Exception as e:
            print(f"[WARNING] Could not load existing attributes.json: {e}")
            attrs = default_attributes
            with open(attributes_path, "w", encoding="utf-8") as f:
                json.dump(attrs, f, indent=4)
    else:
        attrs = default_attributes
        with open(attributes_path, "w", encoding="utf-8") as f:
            json.dump(attrs, f, indent=4)

    # ========== Traverse and build TSV ==========
    rows = []
    all_headers = {"appearance"}  # ensure it exists

    def recurse(obj, parent_chain=None):
        """Walk through nested dicts, recording conductor rows."""
        if parent_chain is None:
            parent_chain = []

        if isinstance(obj, dict):
            # Found conductor
            if obj.get("conductor") is True:
                props = obj.get("properties", {})
                appearance = obj.get("appearance", {})

                # Use previous parent chain to fill in context
                container = parent_chain[-2] if len(parent_chain) >= 2 else ""
                identifier = parent_chain[-1] if len(parent_chain) >= 1 else ""

                row = {"container": container, "identifier": identifier}

                for k, v in props.items():
                    row[k] = v
                    all_headers.add(k)

                # Convert appearance to JSON string (compact)
                row["appearance"] = (
                    json.dumps(
                        appearance, separators=(",", ":"), ensure_ascii=False
                    ).replace('"', "'")
                    if appearance
                    else ""
                )

                rows.append(row)

            # Continue traversing deeper
            for k, v in obj.items():
                if isinstance(v, (dict, list)):
                    recurse(v, parent_chain + [k])

        elif isinstance(obj, list):
            for item in obj:
                recurse(item, parent_chain)

    recurse(attrs)

    if not rows:
        print("[WARNING] No conductor entries found.")
        return

    # Define header order
    headers = ["container", "identifier"] + sorted(all_headers)

    # Write to TSV
    conductor_list_path = fileio.path("conductor list")
    with open(conductor_list_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=headers, delimiter="\t", lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)

    print(
        f"\ncable rendered successfully! wrote {len(rows)} rows to:\n{conductor_list_path}\n"
    )
