import os
import json
import re
from dotenv import load_dotenv
import fileio

def update_harnice_output():
    load_dotenv()

    # Load titleblock setup
    with open(fileio.path("harnice output contents"), "r", encoding="utf-8") as f:
        titleblock_setup = json.load(f)

    # === Root SVG attributes ===
    collected_attrs = {
        "xmlns": "http://www.w3.org/2000/svg",
        "version": "1.1",
        "font-family": "Arial",
        "font-size": "8",
        "width": "1056.0",
        "height": "816.0",
        "viewBox": "0 0 1056.0 816.0"
    }

    # === Build contents for support_do_not_edit-contents_start group ===
    inner_groups = []
    group_position = [0, -1600]
    position_x_delta = 1800

    for tblock_name, tblock_data in titleblock_setup.get("titleblocks", {}).items():
        supplier = os.getenv(tblock_data.get("supplier"))
        titleblock = tblock_data.get("titleblock")
        attr_path = os.path.join(supplier, "titleblocks", titleblock, f"{titleblock}_attributes.json")
        if not os.path.isfile(attr_path):
            raise FileNotFoundError(f"[ERROR] Attribute file not found: {attr_path}")
        with open(attr_path, "r", encoding="utf-8") as f:
            attributes = json.load(f)

        translate_main = f'translate({group_position[0]},{group_position[1]})'
        group_position[0] += position_x_delta

        group = [f'<g id="{tblock_name}" transform="{translate_main}">']

        # Titleblock group
        group.append('<g id="tblock">')
        tblock_svg_path = os.path.join(fileio.dirpath("master_svgs"), f"{fileio.partnumber("pn-rev")}.{tblock_name}_master.svg")
        body, _ = extract_svg_body(tblock_svg_path)
        group.append(body)
        group.append('</g>')

        # BOM group
        bom_loc = attributes.get("periphery_locs", {}).get("bom_loc", [0, 0])
        translate_bom = f'translate({bom_loc[0]},{bom_loc[1]})'
        group.append(f'<g id="bom" transform="{translate_bom}">')
        body, _ = extract_svg_body(fileio.path("bom table master svg"))
        group.append(body)
        group.append('</g>')

        group.append('</g>')  # End outer titleblock group
        inner_groups.append("\n".join(group))

    # Formboard group
    translate_main = f'translate({group_position[0]},{group_position[1]})'
    group = [f'<g id="formboard" transform="{translate_main}">']
    body, _ = extract_svg_body(fileio.path("formboard master svg"))
    group.append(body)
    group.append('</g>')
    inner_groups.append("\n".join(group))
    group_position[0] += position_x_delta
    
    group_start = '<g id="support_do_not_edit-contents_start">\n' + "\n".join(inner_groups) + '\n</g>'
    group_end = '<g id="support_do_not_edit-contents_end"></g>'

    # === Handle existing file ===
    output_path = fileio.path("harnice output")
    if os.path.exists(output_path):
        with open(output_path, "r", encoding="utf-8") as f:
            existing = f.read()

        # Replace <svg ...> tag with new attributes
        new_header = "<svg " + " ".join(f'{k}="{v}"' for k, v in collected_attrs.items()) + ">"
        existing = re.sub(r"<svg[^>]*>", new_header, existing, count=1)

        # Replace contents between support_do_not_edit-contents_start and _end
        pattern = (
            r'<g[^>]*id="support_do_not_edit-contents_start"[^>]*>'  # matches opening group with extra attributes
            r'.*?'                                                   # non-greedy match of inner content
            r'</g>\s*'                                               # closing tag of start group
            r'<g[^>]*id="support_do_not_edit-contents_end"[^>]*/?>'  # matches empty end group (self-closing or not)
        )
        replacement = group_start + '\n' + group_end
        if re.search(pattern, existing, flags=re.DOTALL):
            existing = re.sub(pattern, replacement, existing, flags=re.DOTALL)

        final_output = existing
    else:
        # Create full output from scratch
        svg_attrs = " ".join(f'{k}="{v}"' for k, v in collected_attrs.items())
        final_output = f'<svg {svg_attrs}>\n{group_start}\n{group_end}\n</svg>'

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(final_output)


def extract_svg_body(svg_path):
    if not os.path.isfile(svg_path):
        raise FileNotFoundError(f"[ERROR] SVG file not found: {svg_path}")
    with open(svg_path, "r", encoding="utf-8") as f:
        content = f.read()

    start = content.find("<svg")
    end = content.find("</svg>")
    if start == -1 or end == -1:
        raise ValueError(f"[ERROR] Malformed SVG: {svg_path}")
    body_start = content.find(">", start) + 1

    # Parse attributes from <svg ...>
    header_match = re.search(r'<svg\s+([^>]*)>', content)
    attrs = {}
    if header_match:
        for attr in re.findall(r'(\S+)="([^"]*)"', header_match.group(1)):
            key, value = attr
            attrs[key] = value

    return content[body_start:end].strip(), attrs

def check_group_balance(svg_text):
    open_groups = len(re.findall(r'<g\b[^>]*>', svg_text))
    close_groups = len(re.findall(r'</g>', svg_text))
    if open_groups != close_groups:
        print(f"[WARNING] Unbalanced <g> tags: {open_groups} opening vs {close_groups} closing.")
    else:
        print(f"[OK] Balanced <g> tags: {open_groups} pairs.")
