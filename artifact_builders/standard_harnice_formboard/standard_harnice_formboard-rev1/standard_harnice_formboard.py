import os
import json
from harnice import svg_outputs, flagnotes, rev_history, svg_utils, instances_list, fileio

#=============== PATHS ===============
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