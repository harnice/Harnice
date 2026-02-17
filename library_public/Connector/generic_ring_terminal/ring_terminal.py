import os
import json
import subprocess
from harnice.lists import rev_history
from harnice import state
import harnice.products.part as part
import math

REVISION = "1"
DATE_STARTED = "2/16/26"

STUD_SIZES = {
    "#0": 0.067,
    "#1": 0.08,
    "#2": 0.093,
    "#4": 0.119,
    "#5": 0.132,
    "#6": 0.145,
    "#8": 0.171,
    "#10": 0.197,
    "#12": 0.223,
    "#14": 0.25,
    "1/4": 0.265,
    "5/16": 0.328,
    "3/8": 0.39,
    "7/16": 0.453,
    "1/2": 0.515,
    "5/8": 0.656,
    "3/4": 0.781,
    "7/8": 0.906,
    "1": 1.031
    }

AWG_OD = {
    "4/0": 0.46,
    "3/0": 0.409642,
    "2/0": 0.364797,
    "1/0": 0.324861,
    "1": 0.289297,
    "2": 0.257626,
    "3": 0.229423,
    "4": 0.204307,
    "5": 0.181941,
    "6": 0.162023,
    "7": 0.144285,
    "8": 0.128490,
    "9": 0.114424,
    "10": 0.101897,
    "11": 0.090742,
    "12": 0.080808,
    "13": 0.071962,
    "14": 0.064084,
    "15": 0.057068,
    "16": 0.050821,
    "17": 0.045257,
    "18": 0.040303,
    "19": 0.035891,
    "20": 0.031961,
    "21": 0.028462,
    "22": 0.025347,
    "23": 0.022572,
    "24": 0.020101,
    "25": 0.017900,
    "26": 0.015941,
    "27": 0.014196,
    "28": 0.012641,
    "29": 0.011258,
    "30": 0.010025,
    "31": 0.008928,
    "32": 0.007950,
    "33": 0.007080,
    "34": 0.006305,
    "35": 0.005615,
    "36": 0.005000,
    "37": 0.004453,
    "38": 0.003965,
    "39": 0.003531,
    "40": 0.003145,
}

STANDARD_CSYS_CHILDREN = {
    "flagnote-1": {"angle": 0, "distance": 3, "rotation": 0},
    "flagnote-1-leader_dest": {"angle": 0, "distance": 1, "rotation": 0},
    "flagnote-2": {"angle": 15, "distance": 3, "rotation": 0},
    "flagnote-2-leader_dest": {"angle": 15, "distance": 1.03, "rotation": 0},
    "flagnote-3": {"angle": -15, "distance": 3, "rotation": 0},
    "flagnote-3-leader_dest": {"angle": -15, "distance": 1.03, "rotation": 0},
    "flagnote-4": {"angle": 30, "distance": 3, "rotation": 0},
    "flagnote-4-leader_dest": {"angle": 30, "distance": 1, "rotation": 0},
    "flagnote-5": {"angle": -30, "distance": 3, "rotation": 0},
    "flagnote-5-leader_dest": {"angle": -30, "distance": 1, "rotation": 0},
    "flagnote-6": {"angle": 45, "distance": 3, "rotation": 0},
    "flagnote-6-leader_dest": {"angle": 45, "distance": 0.72, "rotation": 0},
    "flagnote-7": {"angle": -45, "distance": 3, "rotation": 0},
    "flagnote-7-leader_dest": {"angle": -45, "distance": 0.72, "rotation": 0},
    "flagnote-8": {"angle": 60, "distance": 3, "rotation": 0},
    "flagnote-8-leader_dest": {"angle": 60, "distance": 0.58, "rotation": 0},
    "flagnote-9": {"angle": -60, "distance": 3, "rotation": 0},
    "flagnote-9-leader_dest": {"angle": -60, "distance": 0.58, "rotation": 0},
    "flagnote-10": {"angle": -75, "distance": 3, "rotation": 0},
    "flagnote-10-leader_dest": {"angle": -75, "distance": 0.52, "rotation": 0},
    "flagnote-11": {"angle": 75, "distance": 3, "rotation": 0},
    "flagnote-11-leader_dest": {"angle": 75, "distance": 0.52, "rotation": 0},
    "flagnote-12": {"angle": -90, "distance": 3, "rotation": 0},
    "flagnote-12-leader_dest": {"angle": -90, "distance": 0.52, "rotation": 0},
    "flagnote-13": {"angle": 90, "distance": 3, "rotation": 0},
    "flagnote-13-leader_dest": {"angle": 90, "distance": 0.5, "rotation": 0},
}

def compile_part_attributes(part_configuration):
    """
    pn_arrangement = part_configuration.get("insert_arrangement")
    pn_arrangement_prefix = pn_arrangement[0]
    pn_arrangement_suffix = pn_arrangement[1:]

    if pn_arrangement_prefix == "A":
        shell_size = "9"
    elif pn_arrangement_prefix == "B":
        shell_size = "11"
    elif pn_arrangement_prefix == "C":
        shell_size = "13"
    elif pn_arrangement_prefix == "D":
        shell_size = "15"
    elif pn_arrangement_prefix == "E":
        shell_size = "17"
    elif pn_arrangement_prefix == "F":
        shell_size = "19"
    elif pn_arrangement_prefix == "G":
        shell_size = "21"
    elif pn_arrangement_prefix == "H":
        shell_size = "23"
    elif pn_arrangement_prefix == "J":
        shell_size = "25"

    else:
        raise ValueError(f"Invalid insert arrangement prefix: {pn_arrangement_prefix}")

    insert_arrangement = f"{shell_size}-{pn_arrangement_suffix}"
    
    # FIND CONTACTS
    contacts = INSERT_ARRANGEMENTS.get(insert_arrangement)

    # FIND UNIQUE CONTACT SIZES
    seen_contact_sizes = []
    for contact in contacts:
        if contact.get("size") not in seen_contact_sizes:
            seen_contact_sizes.append(contact.get("size"))

    # FIND RELEVANT TOOLS
    tools = []
    for contact_size in seen_contact_sizes:
        tools.append(f"{CONTACT_SIZES.get(contact_size).get('crimp_tool')} crimp tool")
        tools.append(f"{CONTACT_SIZES.get(contact_size).get('extraction_tool')} extraction tool")

    """

    attributes = {
        "tools": None,
        "build_notes": [],
        "csys_children": STANDARD_CSYS_CHILDREN,
        "contacts": None,
        "shell_size": None,
    }
    
    return attributes

def ring_terminal_svg(
    part_number: str,
    stud_id: float,
    ring_od: float,
    wire_od: float,
    overall_length: float,
    insulation: str | None = None,
) -> str:
    """Generate an SVG drawing of a ring terminal.

    All dimensions are in inches.

    Args:
        part_number: Part number used in group IDs.
        stud_id: Stud hole inner diameter.
        ring_od: Ring outer diameter.
        wire_od: Wire / barrel outer diameter.
        overall_length: Overall length from barrel end to ring tip.
        insulation: Hex color string (e.g. "#e03030") or None for bare.

    Returns:
        SVG string.
    """
    ring_r = ring_od / 2
    hole_r = stud_id / 2
    barrel_r = wire_od / 2
    barrel_len = overall_length - ring_od

    scale = 200  # pixels per inch
    pad = 0.15   # inches of padding

    # Origin: far left of barrel, vertically centered
    ox = pad * scale
    oy = (ring_od / 2 + pad) * scale

    # Ring center
    rcx = ox + (overall_length - ring_r) * scale
    rcy = oy

    # Barrel
    bx1 = ox
    bx2 = ox + barrel_len * scale
    by1 = oy - barrel_r * scale
    bh = wire_od * scale

    # Crimp bands
    crimp_w = barrel_len * 0.15
    c1x = bx1 + barrel_len * scale * 0.1
    c2x = bx2 - barrel_len * scale * 0.1 - crimp_w * scale

    # Taper points
    ang = math.atan2(barrel_r, ring_r)
    taper_dx = ring_r * scale * math.cos(ang)
    taper_dy = ring_r * scale * math.sin(ang)

    # SVG dimensions
    svg_w = (overall_length + pad * 2) * scale
    svg_h = (ring_od + pad * 2) * scale

    elements = []

    # Barrel
    elements.append(
        f'<rect x="{bx1:.2f}" y="{by1:.2f}" '
        f'width="{bx2 - bx1 + 2:.2f}" height="{bh:.2f}" '
        f'fill="#898989" rx="2"/>'
    )

    # Taper transition
    pts = (
        f"{rcx - taper_dx:.2f},{rcy - taper_dy:.2f} "
        f"{bx2:.2f},{by1:.2f} "
        f"{bx2:.2f},{by1 + bh:.2f} "
        f"{rcx - taper_dx:.2f},{rcy + taper_dy:.2f}"
    )
    elements.append(f'<polygon points="{pts}" fill="#898989"/>')

    # Ring outer
    elements.append(
        f'<circle cx="{rcx:.2f}" cy="{rcy:.2f}" '
        f'r="{ring_r * scale:.2f}" fill="#898989"/>'
    )

    # Insulation (sharp corners, fully opaque)
    if insulation is not None:
        ins_pad = 1.2 * scale / 6  # same visual ratio as the React version
        ins_x = bx1 - 4
        ins_y = by1 - ins_pad
        ins_h = bh + ins_pad * 2
        ins_w = (c2x + crimp_w * scale / 2) - ins_x
        elements.append(
            f'<rect x="{ins_x:.2f}" y="{ins_y:.2f}" '
            f'width="{ins_w:.2f}" height="{ins_h:.2f}" '
            f'fill="{insulation}"/>'
        )

    # Stud hole
    elements.append(
        f'<circle cx="{rcx:.2f}" cy="{rcy:.2f}" '
        f'r="{hole_r * scale:.2f}" fill="#ffffff" '
        f'stroke="#666666" stroke-width="0.5"/>'
    )

    # Crimp bands (only when no insulation)
    if insulation is None:
        for cx in (c1x, c2x):
            cw = crimp_w * scale
            elements.append(
                f'<rect x="{cx:.2f}" y="{by1:.2f}" '
                f'width="{cw:.2f}" height="{bh:.2f}" '
                f'fill="rgba(0,0,0,0.15)" rx="1"/>'
            )
            elements.append(
                f'<line x1="{cx:.2f}" y1="{by1:.2f}" '
                f'x2="{cx + cw:.2f}" y2="{by1:.2f}" '
                f'stroke="#777777" stroke-width="0.8"/>'
            )
            elements.append(
                f'<line x1="{cx:.2f}" y1="{by1 + bh:.2f}" '
                f'x2="{cx + cw:.2f}" y2="{by1 + bh:.2f}" '
                f'stroke="#777777" stroke-width="0.8"/>'
            )

    # Barrel end opening
    elements.append(
        f'<ellipse cx="{bx1:.2f}" cy="{rcy:.2f}" '
        f'rx="2" ry="{barrel_r * scale:.2f}" '
        f'fill="#6a6a6a" stroke="#777777" stroke-width="0.5"/>'
    )

    # Center crosshair
    elements.append(
        f'<line x1="{rcx - 3:.2f}" y1="{rcy:.2f}" '
        f'x2="{rcx + 3:.2f}" y2="{rcy:.2f}" '
        f'stroke="#bbbbbb" stroke-width="0.5"/>'
    )
    elements.append(
        f'<line x1="{rcx:.2f}" y1="{rcy - 3:.2f}" '
        f'x2="{rcx:.2f}" y2="{rcy + 3:.2f}" '
        f'stroke="#bbbbbb" stroke-width="0.5"/>'
    )

    content = "\n    ".join(elements)

    svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="{svg_w:.0f}" height="{svg_h:.0f}">
<g id="{part_number}-drawing-contents-start">
    {content}
</g>
<g id="{part_number}-drawing-contents-end">
</g>
</svg>'''

    return svg


def main():
    state.set_rev(REVISION)
    state.set_product("part")

    part_configurations = []
    # Common ring terminal configurations: (wire_gauge_range, stud_sizes)
    # Based on typical manufacturer offerings (e.g., 3M, Panduit, Burndy)

    common_combos = [
        # (wire gauges, stud sizes, insulation options)
        # Small insulated terminals (red, blue, yellow color-coded)
        (["22", "20", "18"],        ["#4", "#6", "#8", "#10", "1/4", "5/16", "3/8"], ["#FF0000", None]),
        (["16", "14"],              ["#4", "#6", "#8", "#10", "1/4", "5/16", "3/8"], ["#0000FF", None]),
        (["12", "10"],              ["#6", "#8", "#10", "1/4", "5/16", "3/8", "1/2"], ["#FFFF00", None]),
        # Larger uninsulated / heat shrink terminals
        (["8"],                     ["#8", "#10", "1/4", "5/16", "3/8", "1/2"], [None]),
        (["6"],                     ["#10", "1/4", "5/16", "3/8", "1/2"], [None]),
        (["4"],                     ["1/4", "5/16", "3/8", "1/2", "5/8"], [None]),
        (["3", "2"],                ["1/4", "5/16", "3/8", "1/2", "5/8"], [None]),
        (["1"],                     ["1/4", "5/16", "3/8", "1/2", "5/8", "3/4"], [None]),
        (["1/0"],                   ["1/4", "5/16", "3/8", "1/2", "5/8", "3/4"], [None]),
        (["2/0"],                   ["5/16", "3/8", "1/2", "5/8", "3/4"], [None]),
        (["3/0"],                   ["3/8", "1/2", "5/8", "3/4"], [None]),
        (["4/0"],                   ["3/8", "1/2", "5/8", "3/4", "1"], [None]),
    ]
    for gauges, studs, insulations in common_combos:
        for gauge in gauges:
            for stud in studs:
                for insulation in insulations:
                    part_configurations.append({
                        "wire_gauge": gauge,
                        "stud_size": stud,
                        "insulation": insulation,
                    })
    for part_configuration in part_configurations:
        # GENERATE THE PART NUMBER
        ins = f"-{part_configuration['insulation']}" if part_configuration['insulation'] else ""
        part_number = f"RING_TERMINAL-{part_configuration['wire_gauge']}-{part_configuration['stud_size']}{ins}"
        print("Preparing part number: ", part_number)

        # MAKE THE PART FOLDER
        part_dir = os.path.join(os.getcwd(), part_number)
        os.makedirs(part_dir, exist_ok=True)

        # UPDATE THE REVISION HISTORY FILE
        revision_history_content_dict = {
            "product": state.product,
            "mfg": "mil spec",
            "pn": part_number,
            "rev": REVISION,
            "desc": "",
            "status": "",
            "datestarted": DATE_STARTED,
            "library_repo": "https://github.com/harnice/d38999",
            "library_subpath": "Connector"
        }
        revision_history_csv_path = os.path.join(
            part_dir, f"{part_number}-revision_history.tsv"
        )
        rev_history.part_family_append(
            revision_history_content_dict, revision_history_csv_path
        )

        # CLEAN AND MAKE THE REVISION FOLDER
        rev_dir = os.path.join(part_dir, f"{part_number}-rev{REVISION}")
        if os.path.exists(rev_dir):
            for item in os.listdir(rev_dir):
                item_path = os.path.join(rev_dir, item)
                if os.path.isfile(item_path):
                    os.remove(item_path)
        else:
            os.makedirs(rev_dir)

        # WRITE THE ATTRIBUTES JSON
        json_path = os.path.join(
            rev_dir, f"{part_number}-rev{REVISION}-attributes.json"
        )
        attributes = compile_part_attributes(part_configuration)
        with open(json_path, "w") as f:
            json.dump(attributes, f, indent=2)


        stud_size = STUD_SIZES[part_configuration['stud']]
        wire_od = AWG_OD[part_configuration['wire_gauge']]

        # GENERATE THE SVG
        ring_terminal_svg(
            part_number=part_number,
            stud_id=stud_size,
            ring_od=0.1*stud_size*stud_size + stud_size + 0.1,
            wire_od=wire_od,
            overall_length=4*wire_od,
            insulation=part_configuration['insulation']
        )

        
        # RENDER THE PART
        subprocess.run(['harnice', '-r'], cwd=rev_dir, check=True)

    print("Finished rendering all parts in family.")

if __name__ == "__main__":
    main()
