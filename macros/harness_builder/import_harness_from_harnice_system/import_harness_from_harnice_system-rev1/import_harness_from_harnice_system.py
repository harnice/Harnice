import csv
import os
from harnice import fileio
from harnice.lists import instances_list
from harnice.utils import system_utils

# args:
# system_pn_rev = [pn, rev]
# path_to_system_rev = "Path"
# target_net = "Netname"
# manifest_nets = []

# define the path to the upstream system that this harness will reference
path_to_system_instances_list = os.path.join(
    path_to_system_rev, f"{system_pn_rev[0]}-{system_pn_rev[1]}-instances_list.tsv"
)

# read the system instances list to a variable
system_instances_list_data = []
with open(path_to_system_instances_list, newline="", encoding="utf-8") as f:
    system_instances_list_data = list(csv.DictReader(f, delimiter="\t"))

for instance in system_instances_list_data:
    if instance.get("net") == target_net:
        instances_list.new_instance(instance.get("instance_name"), instance)

fileio.set_net(target_net)

system_utils.update_upstream_manifest(
    path_to_system_rev, system_pn_rev, manifest_nets, fileio.partnumber("pn-rev")
)
