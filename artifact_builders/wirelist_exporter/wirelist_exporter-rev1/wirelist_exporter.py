import csv
import os
import yaml
import xlwt
from os.path import basename
from inspect import currentframe
from harnice import fileio, instances_list

#=============== PATHS ===============
wirelist_output_path = os.path.join(
    fileio.dirpath('artifacts'), "wirelist_exporter",
    f'{fileio.partnumber("pn-rev")}-wirelist.tsv'
)

wirelist_pretty_output_path = os.path.join(
    fileio.dirpath('artifacts'), "wirelist_exporter",
    f'{fileio.partnumber("pn-rev")}-wirelist.xls'
)

#=============== INTERNAL WIRELIST UTILITIES ===============

WIRELIST_COLUMNS = []

def newlist(wirelist_columns_input):
    global WIRELIST_COLUMNS
    WIRELIST_COLUMNS = wirelist_columns_input
    with open(wirelist_output_path, 'w', newline='') as file:
        writer = csv.writer(file, delimiter='\t')
        writer.writerow([col["name"] for col in WIRELIST_COLUMNS])
        writer.writerows([])

def add(row_data):
    column_names = [col["name"] for col in WIRELIST_COLUMNS]
    with open(wirelist_output_path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=column_names, delimiter='\t')
        writer.writerow({key: row_data.get(key, '') for key in column_names})

def tsv_to_xls():
    workbook = xlwt.Workbook()
    sheet = workbook.add_sheet('Sheet1')

    with open(wirelist_output_path, newline='', encoding='utf-8') as tsv_file:
        reader = csv.reader(tsv_file, delimiter='\t')
        headers = next(reader)

        expected_headers = [col["name"] for col in WIRELIST_COLUMNS]
        if headers != expected_headers:
            print("Warning: header mismatch between file and WIRELIST_COLUMNS")

        length_col_idx = None
        for col_idx, header in enumerate(headers):
            if header == "Length (in)":
                length_col_idx = col_idx

            col_config = next((col for col in WIRELIST_COLUMNS if col["name"] == header), {})
            fill_color = col_config.get("fill")
            font_color = col_config.get("font")

            if fill_color or font_color:
                pattern = f'pattern: pattern solid, fore_color {fill_color};' if fill_color else ''
                font = f'font: bold on, color {font_color};' if font_color else 'font: bold on;'
                style = xlwt.easyxf(f'{font} {pattern}')
            else:
                style = xlwt.easyxf('font: bold on;')

            sheet.write(0, col_idx, header, style)

        number_style = xlwt.XFStyle()
        number_format = xlwt.easyxf(num_format_str='0.00').num_format_str
        number_style.num_format_str = number_format

        for row_idx, row in enumerate(reader, start=1):
            for col_idx, cell in enumerate(row):
                if col_idx == length_col_idx:
                    try:
                        sheet.write(row_idx, col_idx, float(cell), number_style)
                    except ValueError:
                        sheet.write(row_idx, col_idx, cell)
                else:
                    sheet.write(row_idx, col_idx, cell)

    workbook.save(wirelist_pretty_output_path)

#=============== CREATE WIRELIST ===============

newlist([
    {"name": "Circuit_name", "fill": "black", "font": "white"},
    {"name": "Length", "fill": "black", "font": "white"},
    {"name": "Cable", "fill": "black", "font": "white"},
    {"name": "Conductor_identifier", "fill": "black", "font": "white"},

    {"name": "From_connector", "fill": "green", "font": "white"},
    {"name": "From_connector_cavity", "fill": "green", "font": "white"},
    {"name": "From_special_contact", "fill": "green", "font": "white"},

    {"name": "To_special_contact", "fill": "red", "font": "white"},
    {"name": "To_connector", "fill": "red", "font": "white"},
    {"name": "To_connector_cavity", "fill": "red", "font": "white"},
])

for instance in instances_list.read_instance_rows():
    if instance.get("item_type") != "Circuit":
        continue

    circuit_name = instance.get("instance_name")
    length = ""
    cable = ""
    conductor_identifier = ""
    from_connector = ""
    from_connector_cavity = ""
    from_special_contact = ""
    to_special_contact = ""
    to_connector = ""
    to_connector_cavity = ""

    # Locate connector cavities
    connector_cavity_counter = 0
    for instance3 in instances_list.read_instance_rows():
        if instance3.get("circuit_id") == circuit_name and instance3.get("item_type") == "Connector cavity":
            if connector_cavity_counter == 0:
                from_connector_cavity = instance3.get("instance_name")
                from_connector = instances_list.attribute_of(from_connector_cavity, "parent_instance")
            elif connector_cavity_counter == 1:
                to_connector_cavity = instance3.get("instance_name")
                to_connector = instances_list.attribute_of(to_connector_cavity, "parent_instance")
            else:
                raise ValueError(
                    f"There are 3 or more cavities specified in circuit {circuit_name} "
                    "but expected two (to, from) when building wirelist."
                )
            connector_cavity_counter += 1

    # Locate special contacts
    for instance4 in instances_list.read_instance_rows():
        if instance4.get("circuit_id") == circuit_name and instance4.get("item_type") == "Contact":
            parent = instance4.get("parent_instance")
            if parent == from_connector:
                from_special_contact = instance4.get("instance_name")
            elif parent == to_connector:
                to_special_contact = instance4.get("instance_name")

    # Locate conductor
    for instance5 in instances_list.read_instance_rows():
        if instance5.get("circuit_id") == circuit_name and instance5.get("item_type") == "Conductor":
            conductor_identifier = instance5.get("print_name")
            cable = instance5.get("parent_instance")
            length = instance5.get("length")

    add({
        "Circuit_name": circuit_name,
        "Length": length,
        "Cable": cable,
        "Conductor_identifier": conductor_identifier,
        "From_connector": instances_list.attribute_of(from_connector, "print_name"),
        "From_connector_cavity": instances_list.attribute_of(from_connector_cavity, "print_name"),
        "From_special_contact": from_special_contact,
        "To_special_contact": to_special_contact,
        "To_connector": instances_list.attribute_of(to_connector, "print_name"),
        "To_connector_cavity": instances_list.attribute_of(to_connector_cavity, "print_name"),
    })

#=============== EXPORT FORMATTED VERSION ===============
tsv_to_xls()
