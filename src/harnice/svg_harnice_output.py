import os
import json
import re
from dotenv import load_dotenv
import fileio
import svg_masters
from lxml import etree as ET

def old_update_harnice_output():
    svg_masters.prep_bom()
    svg_masters.prep_wirelist()

    load_dotenv()

    # Load titleblock setup
    with open(fileio.path("harnice output contents"), "r", encoding="utf-8") as f:
        harnice_output_contents = json.load(f)

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

    for tblock_name, tblock_data in harnice_output_contents.get("titleblocks", {}).items():
        svg_masters.prep_tblock(tblock_name)

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
        group.append(f'<g id="{tblock_name}-contents-start">')
        group.append(f'</g>')
        group.append(f'<g id="{tblock_name}-contents-end"></g>')

        # BOM group
        bom_loc = attributes.get("periphery_locs", {}).get("bom_loc", [0, 0])
        translate_bom = f'translate({bom_loc[0]},{bom_loc[1]})'
        group.append(f'<g id="bom_translated" transform="{translate_bom}">')
        group.append(f'<g id="bom-{tblock_name}-contents-start">')
        group.append(f'</g>')
        group.append(f'<g id="bom-{tblock_name}-contents-end"></g>')
        group.append('</g>')

        group.append('</g>')  # End outer titleblock group

        inner_groups.append("\n".join(group))
    """
    # Formboard group
    for formboard_name, formboard_data in harnice_output_contents.get("formboards", {}).items():
        if "scale" not in formboard_data:
            raise KeyError(f"[ERROR] 'scale' not specified for formboard: {formboard_name}")
        
        scale_key = formboard_data["scale"]
        scales_lookup = harnice_output_contents.get("scales:", {})
        
        if scale_key not in scales_lookup:
            raise KeyError(f"[ERROR] Scale key '{scale_key}' not found in 'scales:' lookup for formboard: {formboard_name}")

        scale_value = scales_lookup[scale_key]

        translate_main = f'translate({group_position[0]},{group_position[1]}) scale({scale_value})'
        group_position[0] += position_x_delta

        group = [f'<g id="{formboard_name}" transform="{translate_main}">']

        # Formboard contents
        body, _ = extract_svg_body(fileio.path("formboard master svg"))

        # Apply opacity="0" to hidden instance IDs
        hide_instances = set(formboard_data.get("hide_instances", []))
        modified_body = []
        for line in body.splitlines():
            if any(f'id="{hid}"' in line for hid in hide_instances):
                if "opacity=" not in line:
                    line = line.replace(">", ' opacity="0">')
                else:
                    line = re.sub(r'opacity="[^"]*"', 'opacity="0"', line)
            modified_body.append(line)

        group.extend(modified_body)
        group.append('</g>')  # End formboard group
        inner_groups.append("\n".join(group))

    # Wirelist group
    translate_main = f'translate({group_position[0]},{group_position[1]})'
    group = [f'<g id="wirelist" transform="{translate_main}">']
    body, _ = extract_svg_body(fileio.path("wirelist master svg"))
    group.append(body)
    group.append('</g>')
    inner_groups.append("\n".join(group))
    group_position[0] += position_x_delta
    """
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

    #go back and replace each item with contents
    for tblock_name, tblock_data in harnice_output_contents.get("titleblocks", {}).items():
        find_and_replace_svg_group(fileio.path("harnice output contents"), source_svg_filepath, source_group_name, destination_group_name):
    
        #group.append(f'<g id="{tblock_name}-contents-start">')
        #group.append(f'<g id="bom-{tblock_name}-contents-start">')

def update_harnice_output():
    if file does not exist fileio.path("harnice output"):

        #initialize the svg
        collected_attrs = {
            "xmlns": "http://www.w3.org/2000/svg",
            "version": "1.1",
            "font-family": "Arial",
            "font-size": "8",
            "width": "1056.0",
            "height": "816.0",
            "viewBox": "0 0 1056.0 816.0"
        }

    else:
        #save entire contents of the svg to a variable
    
    #chatgpt: make a group with id=support-do-not-edit-contents-start

    #track where the contents groups end up
    group_position = [0, -1600]
    position_x_delta = 1800

    #keep track of what to replace later
    groups_to_replace = ''

    #build the group structure of the svg only
    for each svg_master in fileio.dirpath("master_svgs"):
        #append group to support-do-not-edit with id={svg_master}-contents-start and translate=group_position
        #append group to support-do-not-edit with id={svg_master}-contnets-end
        #append svg_master to groups_to_replace

    #add all to svg and save file to 

    #conduct the actual replacement process
    for each svg_master in groups_to_replace:
        find_and_replace_svg_group(
            fileio.path("harnice output contents"), 
            os.path.join(fileio.dirpath("master_svgs"), svg_master), 
            svg_master, 
            svg_master
        )


def extract_svg_body(svg_path):
    if not os.path.isfile(svg_path):
        raise FileNotFoundError(f"[ERROR] SVG file not found: {svg_path}")

    parser = ET.XMLParser(recover=True)
    tree = ET.parse(svg_path, parser=parser)
    root = tree.getroot()

    # Define which tags or namespace fragments to remove
    unwanted_tags = {"defs", "metadata"}
    unwanted_ns_fragments = ("sodipodi", "inkscape")

    # Remove unwanted elements
    for elem in root.xpath("//*"):
        tag = elem.tag
        tag_name = tag.split("}")[-1]  # localname without namespace
        ns_uri = tag.split("}")[0][1:] if "}" in tag else ""

        if (
            tag_name in unwanted_tags or
            any(ns in tag for ns in unwanted_ns_fragments) or
            any(ns in ns_uri for ns in unwanted_ns_fragments)
        ):
            parent = elem.getparent()
            if parent is not None:
                parent.remove(elem)

    # Collect clean root attributes
    allowed_attrs = {
        k: v for k, v in root.attrib.items()
        if not k.startswith("xmlns") and k not in {"version", "viewBox"}
    }

    # Return only child elements as string
    inner_xml = "".join(ET.tostring(child, encoding="unicode") for child in root.iterchildren())
    return inner_xml.strip(), allowed_attrs


def check_group_balance(svg_text):
    open_groups = len(re.findall(r'<g\b[^>]*>', svg_text))
    close_groups = len(re.findall(r'</g>', svg_text))
    if open_groups != close_groups:
        print(f"[WARNING] Unbalanced <g> tags: {open_groups} opening vs {close_groups} closing.")
    else:
        print(f"[OK] Balanced <g> tags: {open_groups} pairs.")
