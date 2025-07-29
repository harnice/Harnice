import os
from harnice import svg_outputs, flagnotes, rev_history, svg_utils, instances_list, fileio



def update_page_setup_json():
    # === Titleblock Defaults ===
    blank_setup = {
        "pages": [
            {
                "name": "page1",
                "supplier": "public",
                "titleblock": "harnice_tblock-11x8.5",
                "text_replacements": {
                    "tblock-key-desc": "pull_from_revision_history(desc)",
                    "tblock-key-pn": "pull_from_revision_history(pn)",
                    "tblock-key-drawnby": "pull_from_revision_history(drawnby)",
                    "tblock-key-rev": "pull_from_revision_history(rev)",
                    "tblock-key-releaseticket": "",
                    "tblock-key-scale": "A",
                    "tblock-key-sheet": "autosheet"
                },
                "show_items": [
                    "bom",
                    "buildnotes",
                    "revhistory"
                ]
            }
        ],
        "formboards": {
            "formboard1": {
                "scale": "A",
                "rotation": 0,
                "hide_instances": {}
            }
        },
        "show_items_example_options":[
            "bom",
            "buildnotes",
            "revhistory"
        ]
    }

    # === Load or Initialize Titleblock Setup ===

    page_setup_path = fileio.dirpath("artifacts")
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

def path(target_value):
    base_path = os.path.join(fileio.dirpath("artifacts"), "standard_harnice_formboard", artifact_id)
    if target_value == "output svg":
        return os.path.join(base_path, f"{fileio.partnumber("pn-rev")}-{artifact_id}-master.svg")
    else:
        raise KeyError(f"Filename {target_value} not found in standard_harnice_formboard file tree")


#=============== REBUILDING OUTPUT SVG #===============
# ensure page setup is defined, if not, make a basic one
page_setup_contents = update_page_setup_json()

revinfo = rev_history.revision_info()

# prepare the building blocks as svgsflagnotes.make_note_drawings()
flagnotes.make_leader_drawings()

#TODO: uncomment this per https://github.com/kenyonshutt/harnice/issues/217
#svg_outputs.prep_formboard_drawings(page_setup_contents)
#svg_outputs.prep_buildnotes_table()

#TODO: add bom processor to svgoutputs https://github.com/kenyonshutt/harnice/issues/226
#svg_outputs.prep_bom()
#svg_outputs.prep_revision_table()

#svg_outputs.prep_tblocks(page_setup_contents, revinfo)

#svg_outputs.prep_master(page_setup_contents)
    # merges all building blocks into one main support_do_not_edit master svg file

svg_outputs.update_harnice_output(page_setup_contents)
    # adds the above to the user-editable svgs in page setup, one per page