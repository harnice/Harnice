import os
import json
import xml.etree.ElementTree as ET
from xml.dom import minidom
import random
import math
import runpy
import re
from harnice import (
    instances_list,
    svg_utils,
    rev_history,
    fileio,
    cli
)

def render():
    print("Thanks for using Harnice!")
    
    # === Step 1: Verify revision and file structure at the top level ===
    fileio.verify_revision_structure()
    fileio.generate_structure()
    rev_history.update_datemodified()

    # === Step 2: Ensure feature_tree.py exists ===
    fileio.verify_feature_tree_exists()
    
    # initialize instances list
    instances_list.make_new_list()
    instances_list.add_unless_exists("origin", {
        "instance_name": "origin",
        "item_type": "Node",
        "location_is_node_or_segment": "Node"
    })

    # === Step 3: Run the project-specific feature_tree.py ===
    runpy.run_path(fileio.path("feature tree"), run_name="__main__")

    print(f"Harnice: harness {fileio.partnumber('pn')} rendered successfully!")
    print()
