import os
from harnice import fileio

def generate_default_feature_tree():
    """
    Creates a default, fully-expanded feature_tree.py in the current part's directory.
    """
    target_path = fileio.path("feature tree")
    os.makedirs(os.path.dirname(target_path), exist_ok=True)

    contents = '''\
from harnice import (
    fileio, instances_list, component_library, wirelist,
    svg_outputs, flagnotes, formboard, run_wireviz, rev_history, svg_utils
)
import os

# === STEP: Setup ===
fileio.verify_revision_structure()
fileio.verify_yaml_exists()
fileio.generate_structure()

# === STEP: Instances ===
instances_list.make_new_list()
instances_list.add_connectors()
instances_list.add_cables()
wirelist.newlist()

# === STEP: Library Sync ===
component_library.pull_parts()

# === STEP: Formboard Construction ===
instances_list.generate_nodes_from_connectors()
instances_list.update_parent_csys()
instances_list.update_component_translate()

if not os.path.exists(fileio.name("formboard graph definition")):
    open(fileio.name("formboard graph definition"), 'w').close()

formboard.validate_nodes()
instances_list.add_nodes_from_formboard()
instances_list.add_segments_from_formboard()
formboard.map_cables_to_segments()
formboard.detect_loops()
formboard.detect_dead_segments()
formboard.generate_node_coordinates()
instances_list.add_cable_lengths()
wirelist.add_lengths()
wirelist.tsv_to_xls()
instances_list.add_absolute_angles_to_segments()
instances_list.add_angles_to_nodes()

# === STEP: BOM ===
instances_list.convert_to_bom()
instances_list.add_bom_line_numbers()

# === STEP: Flagnotes ===
page_setup_contents = svg_outputs.update_page_setup_json()
flagnotes.ensure_manual_list_exists()
flagnotes.compile_all_flagnotes()
instances_list.add_flagnotes()
flagnotes.make_note_drawings()
flagnotes.make_leader_drawings()

# === STEP: Revision Metadata ===
revinfo = rev_history.revision_info()
rev_history.update_datemodified()
instances_list.add_parent_instance_type()

# === STEP: SVG Output ===
svg_outputs.prep_formboard_drawings(page_setup_contents)
svg_outputs.prep_wirelist()
svg_outputs.prep_bom()
svg_outputs.prep_buildnotes_table()
svg_outputs.prep_revision_table()
svg_outputs.prep_tblocks(page_setup_contents, revinfo)
svg_outputs.prep_master(page_setup_contents)
svg_outputs.update_harnice_output(page_setup_contents)
svg_utils.produce_multipage_harnice_output_pdf(page_setup_contents)

# === STEP: Wireviz ===
run_wireviz.generate_esch()
'''

    with open(target_path, "w", encoding="utf-8") as f:
        f.write(contents)
    print(f"[INFO] Created default feature_tree.py at {target_path}")
