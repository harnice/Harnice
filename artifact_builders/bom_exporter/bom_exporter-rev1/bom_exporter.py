import os
import csv
from harnice import instances_list, fileio, svg_outputs

CABLE_MARGIN = 12

BOM_COLUMNS = [
    'bom_line_number', 
    'mpn', 
    'item_type', 
    'qty', 
    'supplier', 
    'total_length_exact',
    'total_length_plus_margin'
]

# make a new file
output_path = os.path.join(fileio.dirpath('artifacts'), "bom_exporter", f'{fileio.partnumber("pn-rev")}-bom.tsv')

with open(output_path, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=BOM_COLUMNS, delimiter='\t')
    writer.writeheader()
    writer.writerows([])

# how to add stuff to the bom file
def add_line_to_bom(line_data):
    with open(output_path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=BOM_COLUMNS, delimiter='\t')
        writer.writerow({key: line_data.get(key, '') for key in BOM_COLUMNS})

# what is the highest bom number in the instances list
highest_bom_number = 0
for instance in instances_list.read_instance_rows():
    if not instance.get("bom_line_number") == "":
        if int(instance.get("bom_line_number")) > highest_bom_number:
            highest_bom_number = int(instance.get("bom_line_number"))

# count the quantities used
qty_counter = 0
for i in range(1, highest_bom_number + 1):
    mpn = ""
    item_type = ""
    qty = 0
    supplier = ""
    total_length_exact = 0
    total_length_plus_margin = 0

    for instance in instances_list.read_instance_rows():
        if not instance.get("bom_line_number") == "":
            if int(instance.get("bom_line_number")) == i:
                mpn = instance.get("mpn")
                item_type = instance.get("item_type")
                qty += 1
                supplier = instance.get("supplier")
                if not instance.get("length") == "":
                    total_length_exact += int(instance.get("length"))
                    total_length_plus_margin += int(instance.get("length")) + CABLE_MARGIN
                else:
                    total_length_exact = ""
                    total_length_plus_margin = ""

    add_line_to_bom({
        'bom_line_number': i,
        'mpn': mpn,
        'item_type': item_type,
        'qty': qty,
        'supplier': supplier,
        'total_length_exact': total_length_exact,
        'total_length_plus_margin': total_length_plus_margin
    })
