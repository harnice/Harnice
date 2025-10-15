import csv
import os
import yaml
import xlwt
from harnice import fileio, instances_list, circuit_instance

artifact_mpn = "circuit_visualizer"

delta_y = 24

node_pointsize = 12
overall_length = 768
whitespace_length = 24

# =============== PATHS ===============
def path(target_value):
    # artifact_path gets passed in as a global from the caller
    if target_value == "circuit visualizer svg":
        return os.path.join(
            artifact_path,
            f"{fileio.partnumber('pn-rev')}-{artifact_id}-circuit-visualizer-master.svg",
        )
    else:
        raise KeyError(
            f"Filename {target_value} not found in wirelist_exporter file tree"
        )

def plot_node(node_name, x, y):
    pass

def plot_segment(segment_name, x, y):
    pass

for instance in instances_list.read_instance_rows():
    y = 0

    if instance.get("item_type") == "Circuit":
        ports = circuit_instance.instances_of_circuit(instance.get("circuit_id"))

        num_nodes = number of nodes in ports
        num_segments = number of segments in ports
        num_whitespaces = num_nodes + num_segments - 1
        segment_length = (overall_length - num_whitespaces * whitespace_length) / num_segments

        x = 0
        for port in ports:
            if instances_list.attribute_of(port, "item_type") == "Node":
                plot_node(port.get("instance_name"), x, y)
                x = x + whitespace_length
            if instances_list.attribute_of(port, "item_type") == "Segment":
                plot_segment(port.get("instance_name"), x, y)
                x = x + segment_length

        y = y + delta_y