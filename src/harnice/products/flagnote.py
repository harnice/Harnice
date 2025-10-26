import os
import json
import random
import math
from harnice import fileio, cli

def file_structure():
    return {}

def generate_structure():
    pass

def render():
    print(
        "Warning: rendering a flagnote may clear user edits to its svg. Do you wish to proceed?"
    )
    if cli.prompt("Press enter to confirm or any key to exit") == "":
        exit()

    fileio.verify_revision_structure(product_type="flagnote")
    params_path = fileio.path("params")

    # Geometry generators
    def regular_ngon(n, radius=19.2, rotation_deg=0):
        angle_offset = math.radians(rotation_deg)
        return [
            [
                round(radius * math.cos(2 * math.pi * i / n + angle_offset), 2),
                round(radius * math.sin(2 * math.pi * i / n + angle_offset), 2),
            ]
            for i in range(n)
        ]

    def right_arrow():
        return [[-24, -12], [0, -12], [0, -24], [24, 0], [0, 24], [0, 12], [-24, 12]]

    def left_arrow():
        return [[24, -12], [0, -12], [0, -24], [-24, 0], [0, 24], [0, 12], [24, 12]]

    def flag_pennant():
        return [[-24, -12], [24, 0], [-24, 12]]

    # List of shape options with (label, generator)
    shape_options = [
        ("circle", None),
        ("square", lambda: regular_ngon(4, rotation_deg=45)),
        ("triangle", lambda: regular_ngon(3, rotation_deg=-90)),
        ("upside down triangle", lambda: regular_ngon(3, rotation_deg=90)),
        ("hexagon", lambda: regular_ngon(6)),
        ("pentagon", lambda: regular_ngon(5)),
        ("right arrow", right_arrow),
        ("left arrow", left_arrow),
        ("octagon", lambda: regular_ngon(8)),
        ("diamond", lambda: regular_ngon(4, rotation_deg=0)),
        ("flag / pennant", flag_pennant),
    ]

    # === Prompt shape if no params exist ===
    if not os.path.exists(params_path):
        print("No flagnote params found.")
        print("Choose a shape for your flagnote:")
        for i, (label, _) in enumerate(shape_options, 1):
            print(f"  {i}) {label}")

        while True:
            response = cli.prompt("Enter the number of your choice").strip()
            if response.isdigit():
                index = int(response)
                if 1 <= index <= len(shape_options):
                    shape_label, shape_func = shape_options[index - 1]
                    break
            print("Invalid selection. Please enter a number from the list.")

        params = {"fill": 0xFFFFFF, "border": 0x000000, "text inside": "flagnote-text"}

        if shape_func:
            params["vertices"] = shape_func()

        with open(params_path, "w", encoding="utf-8") as f:
            json.dump(params, f, indent=2)

    # === Load params ===
    with open(params_path, "r", encoding="utf-8") as f:
        p = json.load(f)

    svg_width = 6 * 96
    svg_height = 6 * 96

    fill = p.get("fill")
    if not isinstance(fill, int):
        fill = random.randint(0x000000, 0xFFFFFF)

    border = p.get("border", 0x000000)
    shape_svg = ""

    # === Shape element ===
    if "vertices" in p:
        if p["vertices"]:
            points_str = " ".join(f"{x},{y}" for x, y in p["vertices"])
            shape_svg = f'    <polygon points="{points_str}" fill="#{fill:06X}" stroke="#{border:06X}"/>\n'
    else:
        shape_svg = f'    <circle cx="0" cy="0" r="10" fill="#{fill:06X}" stroke="#{border:06X}"/>\n'

    # === Text element ===
    text_content = p.get("text inside", "")
    text_svg = (
        f'    <text x="0" y="0" '
        f'style="font-size:8px;font-family:Arial" '
        f'text-anchor="middle" dominant-baseline="middle" id="flagnote-text">{text_content}</text>\n'
    )

    contents = shape_svg + text_svg if shape_svg else ""

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="{svg_width}" height="{svg_height}">',
        f'  <g id="{fileio.partnumber('pn')}-drawing-contents-start">',
        contents.rstrip(),
        "  </g>",
        f'  <g id="{fileio.partnumber('pn')}-drawing-contents-end">',
        "  </g>",
        "</svg>",
    ]

    with open(fileio.path("drawing"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print()
    print(f"Flagnote '{fileio.partnumber('pn')}' updated")
    print()
