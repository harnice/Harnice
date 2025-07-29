import os
import json
from harnice import svg_outputs, flagnotes, rev_history, svg_utils, instances_list, fileio

#=============== PATHS ===============
def path(target_value):
    base_path = os.path.join(fileio.dirpath("artifacts"), "standard_harnice_formboard", artifact_id)
    if target_value == "output svg":
        return os.path.join(base_path, f"{fileio.partnumber("pn-rev")}-{artifact_id}-master.svg")
    if target_value == "show hide":
        return os.path.join(base_path, f"{fileio.partnumber("pn-rev")}-{artifact_id}-showhide.json")
    else:
        raise KeyError(f"Filename {target_value} not found in standard_harnice_formboard file tree")

def update_harnice_output(page_setup_contents):
    for page_data in page_setup_contents.get("pages", []):
        page_name = page_data.get("name")
        filename = f"{fileio.partnumber('pn-rev')}.{page_name}.svg"
        filepath = os.path.join(fileio.dirpath("page_setup"), filename)

        #pull PDF size from json in library
        titleblock_supplier = page_data.get("supplier")
        titleblock = page_data.get("titleblock", {})
        attr_library_path = os.path.join(
            fileio.dirpath("tblock_svgs"),
            page_name,
            f"{page_name}-attributes.json"
        )
        with open(attr_library_path, "r", encoding="utf-8") as f:
            tblock_attributes = json.load(f)
        page_size_in = tblock_attributes.get("page_size_in", {})
        page_size_px = [page_size_in[0] * 96, page_size_in[1] * 96]
        
        if not os.path.exists(filepath):
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(
                    #<?xml version="1.0" encoding="UTF-8" standalone="no"?>
                    f"""
        <svg xmlns="http://www.w3.org/2000/svg"
            xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape"
            version="1.1"
            width="{page_size_px[0]}"
            height="{page_size_px[1]}">
            <g id="tblock-svg-contents-start">
            </g>
            <g id="tblock-svg-contents-end"></g>
            <g id="svg-master-contents-start">
            </g>
            <g id="svg-master-contents-end"></g>
        </svg>
        """)

        #replace the master svg
        svg_utils.find_and_replace_svg_group(
            filepath, 
            fileio.path("master svg"), 
            "svg-master", 
            "svg-master"
        )

        #replace the titleblock
        svg_utils.find_and_replace_svg_group(
            filepath, 
            os.path.join(fileio.dirpath("tblock_svgs"), page_name, f"{page_name}.svg"),
            page_name, 
            "tblock-svg"
        )


def update_showhide():
    # === Titleblock Defaults ===
    blank_setup = {
        "hide_instances":{},
        "hide_item_types":{}
    }

    # === Load or Initialize Titleblock Setup ===
    if not os.path.exists(path("output svg")) or os.path.getsize(path("output svg")) == 0:
        with open(path("output svg"), "w", encoding="utf-8") as f:
            json.dump(blank_setup, f, indent=4)
        tblock_data = blank_setup
    else:
        try:
            with open(path("output svg"), "r", encoding="utf-8") as f:
                tblock_data = json.load(f)
        except json.JSONDecodeError:
            with open(path("output svg"), "w", encoding="utf-8") as f:
                json.dump(blank_setup, f, indent=4)
            tblock_data = blank_setup

    with open(path("output svg"), "w", encoding="utf-8") as f:
        json.dump(tblock_data, f, indent=4)

    return tblock_data


#=============== REBUILDING OUTPUT SVG #===============
# ensure page setup is defined, if not, make a basic one
showhide = ()

revinfo = rev_history.revision_info()

# prepare the building blocks as svgsflagnotes.make_note_drawings()
#TODO: uncomment this per https://github.com/kenyonshutt/harnice/issues/217
#flagnotes.make_leader_drawings()

#TODO: uncomment this per https://github.com/kenyonshutt/harnice/issues/217
#svg_outputs.prep_formboard_drawings(page_setup_contents)
#svg_outputs.prep_buildnotes_table()

#TODO: add bom processor to svgoutputs https://github.com/kenyonshutt/harnice/issues/226
#svg_outputs.prep_bom()
#svg_outputs.prep_revision_table()

#svg_outputs.prep_tblocks(page_setup_contents, revinfo)

#svg_outputs.prep_master(page_setup_contents)
    # merges all building blocks into one main support_do_not_edit master svg file

update_harnice_output(page_setup_contents)
    # adds the above to the user-editable svgs in page setup, one per page