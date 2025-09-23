import csv
import os
from harnice import instances_list

# args:
# system_pn_rev = [pn, rev]
# path_to_system_rev = "Path"
# target_net = "Netname"

path_to_system_instances_list = os.path.join(
    path_to_system, f"{system_pn_rev[0]}-rev{system_pn_rev[1]}-instances_list.tsv"
)
system_instances_list_data = []

# read the system instances list to a variable
with open(path_to_system_instances_list, newline="", encoding="utf-8") as f:
    system_instances_list_data = list(csv.DictReader(f, delimiter="\t"))

for instance in system_instances_list_data:
    if instance.get("net") == target_net:
        instances_list.add_unless_exists(instance.get("instance_name"), instance)
