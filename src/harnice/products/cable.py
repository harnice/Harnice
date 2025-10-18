import os
import csv
from harnice import fileio
import json


def render():
    fileio.verify_revision_structure(product_type="cable")

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
                    "properties": {
                        "gauge": "20AWG",
                        "construction": "7x28",
                    },
                },
                "pair_1": {
                    "properties": {
                        "twists": "12 per inch",
                    },
                    "black": {
                        "conductor": True,
                        "properties": {
                            "insulation material": "polyethylene",
                            "od": "0.017in",
                            "gauge": "20AWG",
                            "construction": "7x28",
                            "material": "copper",
                        },
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
                    },
                },
            },
        }
    }

    attributes_path = fileio.path("attributes")

    # ========= add default to attributes, if already exists, return it as attrs
    # Load or create attributes.json
    if os.path.exists(attributes_path):
        try:
            with open(attributes_path, "r", encoding="utf-8") as f:
                attrs = json.load(f)
        except Exception as e:
            print(f"[WARNING] Could not load existing attributes.json: {e}")
            attrs = default_attributes.copy()
            # Re-write with defaults to fix the bad file
            with open(attributes_path, "w", encoding="utf-8") as f:
                json.dump(attrs, f, indent=4)
    else:
        attrs = default_attributes.copy()
        with open(attributes_path, "w", encoding="utf-8") as f:
            json.dump(attrs, f, indent=4)

    # ========== write conductor list from json ==========
    rows = []
    all_headers = set()

    def recurse(obj, grandparent_key=None, parent_key=None):
        if isinstance(obj, dict):
            # Check if this dict defines a conductor
            if obj.get("conductor") is True:
                props = obj.get("properties", {})
                row = {"container": grandparent_key, "identifier": parent_key}
                for k, v in props.items():
                    row[k] = v
                    all_headers.add(k)
                rows.append(row)
            else:
                # Keep traversing
                for k, v in obj.items():
                    recurse(v, grandparent_key=parent_key, parent_key=k)
        elif isinstance(obj, list):
            for item in obj:
                recurse(item, grandparent_key=grandparent_key, parent_key=parent_key)

    recurse(attrs)

    # Define header order
    headers = ["container", "identifier"] + sorted(all_headers)

    # Write to TSV
    with open(fileio.path("conductor list"), "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=headers, delimiter="\t", lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)

    print("\nCable rendered successfully!\n")
