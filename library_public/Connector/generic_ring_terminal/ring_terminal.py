import os
import json
import subprocess
import math
from harnice.lists import rev_history
from harnice import state

REVISION = "1"
DATE_STARTED = "2/16/26"

# ---------------------------------------------------------------------------
# Reference data
# ---------------------------------------------------------------------------

STUD_SIZES = {
    "#0": 0.067,  "#1": 0.08,   "#2": 0.093,  "#4": 0.119,
    "#5": 0.132,  "#6": 0.145,  "#8": 0.171,  "#10": 0.197,
    "#12": 0.223, "#14": 0.25,
    "1/4": 0.265, "5/16": 0.328, "3/8": 0.39, "7/16": 0.453,
    "1/2": 0.515, "5/8": 0.656, "3/4": 0.781, "7/8": 0.906,
    "1": 1.031,
}

AWG_OD = {
    "4/0": 0.46,     "3/0": 0.409642, "2/0": 0.364797, "1/0": 0.324861,
    "1": 0.289297,   "2": 0.257626,   "3": 0.229423,   "4": 0.204307,
    "5": 0.181941,   "6": 0.162023,   "7": 0.144285,   "8": 0.128490,
    "9": 0.114424,   "10": 0.101897,  "11": 0.090742,  "12": 0.080808,
    "13": 0.071962,  "14": 0.064084,  "15": 0.057068,  "16": 0.050821,
    "17": 0.045257,  "18": 0.040303,  "19": 0.035891,  "20": 0.031961,
    "21": 0.028462,  "22": 0.025347,  "23": 0.022572,  "24": 0.020101,
    "25": 0.017900,  "26": 0.015941,  "27": 0.014196,  "28": 0.012641,
    "29": 0.011258,  "30": 0.010025,  "31": 0.008928,  "32": 0.007950,
    "33": 0.007080,  "34": 0.006305,  "35": 0.005615,  "36": 0.005000,
    "37": 0.004453,  "38": 0.003965,  "39": 0.003531,  "40": 0.003145,
}

# Approximate ampacity for copper ring terminals (free-air, single conductor).
# Conservative values — derate for bundled / enclosed installations.
AWG_AMPACITY = {
    "4/0": 230, "3/0": 200, "2/0": 175, "1/0": 150,
    "1": 130,   "2": 115,   "3": 100,   "4": 85,
    "5": 75,    "6": 65,    "7": 55,    "8": 50,
    "9": 40,    "10": 35,   "12": 25,   "14": 20,
    "16": 13,   "18": 10,   "20": 7,    "22": 5,
}

# Standard insulation colour coding per wire-gauge band
INSULATION_COLORS = {
    "red":    "#FF0000",  # 22-18 AWG
    "blue":   "#0000FF",  # 16-14 AWG
    "yellow": "#FFFF00",  # 12-10 AWG
}


def terminal_outline_distance(
    angle_deg: float,
    ring_od: float,
    overall_length: float,
    padding: float = 0.04,
) -> float:
    """Distance from center of a rounded rectangle to its perimeter at a given angle.

    The terminal silhouette is approximated as a rounded rectangle:
      - width  = overall_length
      - height = ring_od
      - corner radius = ring_od / 2  (so the ring end is a perfect semicircle)

    The centroid sits at the geometric center of this rounded rect.

    Args:
        angle_deg: Angle in degrees (0 = toward ring tip, 90 = up, 180 = barrel end).
        ring_od: Ring outer diameter (sets height AND corner radius).
        overall_length: Overall terminal length (sets width).
        padding: Extra gap beyond the surface.

    Returns:
        Distance from centroid to perimeter + padding.
    """
    r = ring_od / 2            # corner radius = half the height
    hh = r                     # half-height equals corner radius

    # Since hh == r, the inner rect has zero vertical extent (iy = 0),
    # so arc centers sit along the x-axis at y = 0.
    ix = overall_length - r  # distance between origin and beginning of ring

    ang = math.radians(angle_deg)
    cos_a = math.cos(ang)
    sin_a = math.sin(ang)

    # Ray from origin: P(t) = t * (cos_a, sin_a), t > 0.
    # A rounded rect with hh == r has only two zone types:
    #   - Flat top/bottom edges (between the two arc centers)
    #   - Semicircular caps on left and right

    # --- Flat top/bottom: y = ±hh, x in [-ix, ix] ---
    t_best = math.inf
    if abs(sin_a) > 1e-12:
        for edge_y in (hh, -hh):
            t = edge_y / sin_a
            if t > 1e-9:
                x_hit = t * cos_a
                if -ix - 1e-9 <= x_hit <= ix + 1e-9:
                    t_best = min(t_best, t)

    # --- Semicircular caps centered at (±ix, 0), radius r ---
    for cx in (ix, -ix):
        # |P(t) - (cx, 0)|^2 = r^2
        # t^2 - 2*t*cos_a*cx + cx^2 - r^2 = 0
        b = -2.0 * cos_a * cx
        c = cx * cx - r * r
        disc = b * b - 4.0 * c
        if disc >= 0:
            sqrt_d = math.sqrt(disc)
            for sign in (1, -1):
                t = (-b + sign * sqrt_d) / 2.0
                if t > 1e-9:
                    # Verify the hit is in the cap's angular domain:
                    # Right cap (cx = +ix): hit x >= ix
                    # Left cap  (cx = -ix): hit x <= -ix
                    x_hit = t * cos_a
                    if (cx > 0 and x_hit >= cx - 1e-9) or (cx < 0 and x_hit <= cx + 1e-9):
                        t_best = min(t_best, t)

    if t_best == math.inf:
        # Fallback — should not happen for well-formed inputs
        return overall_length / 2 + padding

    return t_best + padding


def build_csys_children(
    ring_od: float,
    overall_length: float,
    num_flagnotes: int = 13,
    label_distance: float = 3.0,
    padding: float = 0.04,
) -> dict:
    """Build csys_children with leader_dest points on the rounded-rect outline.

    Angles are distributed symmetrically: 0, ±15, ±30, …
    """
    angles = [0]
    step = 15
    a = step
    while len(angles) < num_flagnotes:
        angles.append(a)
        if len(angles) < num_flagnotes:
            angles.append(-a)
        a += step

    children = {}
    for i, angle in enumerate(angles, start=1):
        dest_dist = terminal_outline_distance(
            angle, ring_od, overall_length, padding=padding,
        )
        children[f"flagnote-{i}"] = {
            "angle": angle, "distance": label_distance, "rotation": 0,
        }
        children[f"flagnote-{i}-leader_dest"] = {
            "angle": angle, "distance": round(dest_dist, 4), "rotation": 0,
        }

    return children

# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------

def ring_od_from_stud(stud_id: float) -> float:
    """Compute ring OD from stud hole diameter.

    TODO: Replace with manufacturer-specific lookup if available.
    """
    return 0.2 * stud_id * stud_id + stud_id + 0.2


def overall_length_from_wire(barrel_od: float, ring_od: float) -> float:
    """Compute overall terminal length from wire OD and ring OD.

    TODO: Replace with manufacturer-specific lookup if available.
    """
    return 2 * barrel_od + ring_od


# ---------------------------------------------------------------------------
# Attribute compilation
# ---------------------------------------------------------------------------

def compile_part_attributes(cfg: dict) -> dict:
    """Build the attributes dict for a single ring terminal configuration."""
    wire_gauge = cfg["wire_gauge"]
    stud_size_label = cfg["stud_size"]
    insulation = cfg["insulation"]

    stud_id = STUD_SIZES[stud_size_label]
    wire_od = AWG_OD[wire_gauge]
    ring_od = ring_od_from_stud(stud_id)
    barrel_od = wire_od + 0.15  # shank diameter
    length = overall_length_from_wire(barrel_od, ring_od)
    ampacity = AWG_AMPACITY.get(wire_gauge)

    return {
        # Identification
        "wire_gauge_awg": wire_gauge,
        "stud_size": stud_size_label,
        "insulation_color": insulation,
        "insulated": insulation is not None,

        # Key dimensions (inches)
        "stud_hole_id": round(stud_id, 4),
        "ring_od": round(ring_od, 4),
        "barrel_od": round(barrel_od, 4),
        "overall_length": round(length, 4),

        # Electrical
        "ampacity_a": ampacity,
        "voltage_rating_v": 600,  # typical for most commercial terminals

        # Material defaults (override per-manufacturer as needed)
        "barrel_material": "copper",
        "plating": "tin",
        "insulation_material": "vinyl" if insulation else None,

        # Crimp tooling — populate from manufacturer data
        "crimp_tool": None,
        "crimp_die": None,

        # Drawing / harnice metadata
        "tools": None,
        "build_notes": [],
        "csys_children": build_csys_children(
            ring_od=ring_od,
            overall_length=length,
        ),
        "contacts": None,
        "shell_size": None,
    }


# ---------------------------------------------------------------------------
# SVG generation
# ---------------------------------------------------------------------------

def ring_terminal_svg(
    part_number: str,
    stud_id: float,
    ring_od: float,
    barrel_od: float,
    overall_length: float,
    insulation: str | None = None,
) -> str:
    """Generate an SVG drawing of a ring terminal.

    All dimensions are in inches.

    Args:
        part_number: Part number used in group IDs.
        stud_id: Stud hole inner diameter.
        ring_od: Ring outer diameter.
        barrel_od: Barrel / shank outer diameter.
        overall_length: Overall length from barrel end to ring tip.
        insulation: Hex colour string (e.g. "#e03030") or None for bare.

    Returns:
        SVG markup string.
    """
    ring_r = ring_od / 2
    hole_r = stud_id / 2
    barrel_r = barrel_od / 2
    barrel_len = overall_length - ring_od

    scale = 96   # pixels per inch

    # Ring center
    rcx = (overall_length - ring_r) * scale
    rcy = 0

    # Barrel rectangle
    bx1 = 0
    bx2 = barrel_len * scale
    by1 = -barrel_r * scale
    bh = barrel_od * scale

    # Crimp bands
    crimp_w = barrel_len * 0.15
    c1x = barrel_len * scale * 0.1
    c2x = bx2 - barrel_len * scale * 0.1 - crimp_w * scale

    # Taper from barrel to ring
    ang = math.atan2(barrel_r, ring_r)
    taper_dx = ring_r * scale * math.cos(ang)
    taper_dy = ring_r * scale * math.sin(ang)

    svg_w = overall_length * scale
    svg_h = max(ring_od, barrel_od) * scale

    els: list[str] = []

    # Barrel body
    els.append(
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
    els.append(f'<polygon points="{pts}" fill="#898989"/>')

    # Ring outer disc
    els.append(
        f'<circle cx="{rcx:.2f}" cy="{rcy:.2f}" '
        f'r="{ring_r * scale:.2f}" fill="#898989"/>'
    )

    # Insulation sleeve
    if insulation is not None:
        ins_pad = 0.15 * scale / 6
        ins_x = bx1 - 4
        ins_y = by1 - ins_pad
        ins_h = bh + ins_pad * 2
        ins_w = (c2x + crimp_w * scale / 2) - ins_x
        els.append(
            f'<rect x="{ins_x:.2f}" y="{ins_y:.2f}" '
            f'width="{ins_w:.2f}" height="{ins_h:.2f}" '
            f'fill="{insulation}"/>'
        )

    # Stud hole
    els.append(
        f'<circle cx="{rcx:.2f}" cy="{rcy:.2f}" '
        f'r="{hole_r * scale:.2f}" fill="#ffffff" '
        f'stroke="#666666" stroke-width="0.5"/>'
    )

    # Crimp bands (bare terminals only)
    if insulation is None:
        for cx in (c1x, c2x):
            cw = crimp_w * scale
            els.append(
                f'<rect x="{cx:.2f}" y="{by1:.2f}" '
                f'width="{cw:.2f}" height="{bh:.2f}" '
                f'fill="rgba(0,0,0,0.15)" rx="1"/>'
            )
            for y in (by1, by1 + bh):
                els.append(
                    f'<line x1="{cx:.2f}" y1="{y:.2f}" '
                    f'x2="{cx + cw:.2f}" y2="{y:.2f}" '
                    f'stroke="#777777" stroke-width="0.8"/>'
                )

        # Barrel end opening (bare terminals only)
        els.append(
            f'<ellipse cx="{bx1:.2f}" cy="{rcy:.2f}" '
            f'rx="2" ry="{barrel_r * scale:.2f}" '
            f'fill="#6a6a6a" stroke="#777777" stroke-width="0.5"/>'
        )

    # Center crosshair
    for dx, dy in [(3, 0), (0, 3)]:
        els.append(
            f'<line x1="{rcx - dx:.2f}" y1="{rcy - dy:.2f}" '
            f'x2="{rcx + dx:.2f}" y2="{rcy + dy:.2f}" '
            f'stroke="#bbbbbb" stroke-width="0.5"/>'
        )

    content = "\n    ".join(els)
    return (
        f'<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" version="1.1"'
        f' width="{svg_w:.0f}" height="{svg_h:.0f}">\n'
        f'<g id="{part_number}-drawing-contents-start">\n'
        f'    {content}\n'
        f'</g>\n'
        f'<g id="{part_number}-drawing-contents-end">\n'
        f'</g>\n'
        f'</svg>'
    )


# ---------------------------------------------------------------------------
# Part-family generation matrix
# ---------------------------------------------------------------------------

# (wire gauges, stud sizes, insulation options)
COMMON_COMBOS = [
    # Small insulated terminals (colour-coded red / blue / yellow)
    (["22", "20", "18"], ["#4", "#6", "#8", "#10", "1/4", "5/16", "3/8"],
     ["#FF0000", None]),
    (["16", "14"],       ["#4", "#6", "#8", "#10", "1/4", "5/16", "3/8"],
     ["#0000FF", None]),
    (["12", "10"],       ["#6", "#8", "#10", "1/4", "5/16", "3/8", "1/2"],
     ["#FFFF00", None]),
    # Larger bare terminals
    (["8"],              ["#8", "#10", "1/4", "5/16", "3/8", "1/2"],        [None]),
    (["6"],              ["#10", "1/4", "5/16", "3/8", "1/2"],              [None]),
    (["4"],              ["1/4", "5/16", "3/8", "1/2", "5/8"],             [None]),
    (["3", "2"],         ["1/4", "5/16", "3/8", "1/2", "5/8"],             [None]),
    (["1"],              ["1/4", "5/16", "3/8", "1/2", "5/8", "3/4"],      [None]),
    (["1/0"],            ["1/4", "5/16", "3/8", "1/2", "5/8", "3/4"],      [None]),
    (["2/0"],            ["5/16", "3/8", "1/2", "5/8", "3/4"],             [None]),
    (["3/0"],            ["3/8", "1/2", "5/8", "3/4"],                     [None]),
    (["4/0"],            ["3/8", "1/2", "5/8", "3/4", "1"],                [None]),
]


def build_part_configurations() -> list[dict]:
    """Expand the combo matrix into individual part configurations."""
    configs = []
    for gauges, studs, insulations in COMMON_COMBOS:
        for gauge in gauges:
            for stud in studs:
                for ins in insulations:
                    configs.append({
                        "wire_gauge": gauge,
                        "stud_size": stud,
                        "insulation": ins,
                    })
    return configs


def part_number_from_cfg(cfg: dict) -> str:
    """Derive a part number string from a configuration dict."""
    gauge = cfg["wire_gauge"].lstrip("#").replace("/", "_")
    stud = cfg["stud_size"].lstrip("#").replace("/", "_")
    ins = f"-{cfg['insulation'].lstrip('#')}" if cfg["insulation"] else ""
    return f"RING_TERMINAL-{gauge}-{stud}{ins}"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    state.set_rev(REVISION)
    state.set_product("part")

    for cfg in build_part_configurations():
        pn = part_number_from_cfg(cfg)
        print(f"Preparing part number: {pn}")

        # ---- directory structure ----
        part_dir = os.path.join(os.getcwd(), pn)
        os.makedirs(part_dir, exist_ok=True)

        rev_dir = os.path.join(part_dir, f"{pn}-rev{REVISION}")
        if os.path.exists(rev_dir):
            for item in os.listdir(rev_dir):
                p = os.path.join(rev_dir, item)
                if os.path.isfile(p):
                    os.remove(p)
        else:
            os.makedirs(rev_dir)

        # ---- revision history ----
        rev_history.part_family_append(
            {
                "product": state.product,
                "mfg": "mil spec",
                "pn": pn,
                "rev": REVISION,
                "desc": "",
                "status": "",
                "datestarted": DATE_STARTED,
                "library_repo": "https://github.com/harnice/d38999",
                "library_subpath": "Connector",
            },
            os.path.join(part_dir, f"{pn}-revision_history.tsv"),
        )

        # ---- attributes JSON ----
        attributes = compile_part_attributes(cfg)
        json_path = os.path.join(rev_dir, f"{pn}-rev{REVISION}-attributes.json")
        with open(json_path, "w") as f:
            json.dump(attributes, f, indent=2)

        # ---- SVG drawing ----
        svg_content = ring_terminal_svg(
            part_number=pn,
            stud_id=attributes["stud_hole_id"],
            ring_od=attributes["ring_od"],
            barrel_od=attributes["barrel_od"],
            overall_length=attributes["overall_length"],
            insulation=cfg["insulation"],
        )
        svg_path = os.path.join(rev_dir, f"{pn}-rev{REVISION}-drawing.svg")
        with open(svg_path, "w") as f:
            f.write(svg_content)

        # ---- render ----
        subprocess.run(["harnice", "-r"], cwd=rev_dir, check=True)

    print("Finished rendering all parts in family.")


if __name__ == "__main__":
    main()