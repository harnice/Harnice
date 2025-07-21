#=============== REBUILDING OUTPUT SVG #===============
# ensure page setup is defined, if not, make a basic one
page_setup_contents = svg_outputs.update_page_setup_json()

revinfo = rev_history.revision_info()

# add parent types to make filtering easier
instances_list.add_parent_instance_type()

# prepare the building blocks as svgsflagnotes.make_note_drawings()
flagnotes.make_leader_drawings()
svg_outputs.prep_formboard_drawings(page_setup_contents)
svg_outputs.prep_bom()
svg_outputs.prep_buildnotes_table()
svg_outputs.prep_revision_table()
# esch done under run_wireviz.generate_esch()

svg_outputs.prep_tblocks(page_setup_contents, revinfo)

svg_outputs.prep_master(page_setup_contents)
    # merges all building blocks into one main support_do_not_edit master svg file

svg_outputs.update_harnice_output(page_setup_contents)
    # adds the above to the user-editable svgs in page setup, one per page

svg_utils.produce_multipage_harnice_output_pdf(page_setup_contents)
    # makes a PDF out of each svg in page setup
