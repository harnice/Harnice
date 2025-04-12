import yaml
import csv
import os
from os.path import basename
from inspect import currentframe
import fileio
import yaml
import csv
from os.path import basename
from inspect import currentframe

def newlist():
    try:
        with open(fileio.path("harness yaml"), 'r') as file:
            yaml_data = yaml.safe_load(file)
    except FileNotFoundError:
        print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Error: {fileio.name('harness yaml')} not found in the current directory.")
        exit(1)

    # Extract connections and build wirelist
    connections = yaml_data.get("connections", [])
    wirelist = []

    for group in connections:
        components = {list(item.keys())[0]: list(item.values())[0] for item in group}
        wire = None
        targets = []

        for component, pins in components.items():
            if component.startswith("W"):
                wire = (component, pins)
            elif component.startswith("X"):
                targets.append((component, pins))

        if wire and len(targets) == 2:
            wire_name, wire_pins = wire
            src_component, src_pins = targets[0]
            dst_component, dst_pins = targets[1]

            for i in range(len(wire_pins)):
                wire_pin = wire_pins[i]
                src_pin = src_pins[i] if isinstance(src_pins, list) else src_pins
                dst_pin = dst_pins[i] if isinstance(dst_pins, list) else dst_pins

                wirelist.append([
                    wire_name, wire_pin,
                    src_component, src_pin,
                    dst_component, dst_pin
                ])

    with open(fileio.path("wirelist no formats"), 'w', newline='') as file:
        writer = csv.writer(file, delimiter='\t')
        writer.writerow(["Wire", "Subwire", "Subwire Color","Source", "SourcePin", "WireLabel at Source", "SubwireLabel at Source", "Destination", "DestinationPin", "WireLabel at Destination", "SubwireLabel at Destination"])
        writer.writerows(wirelist)

def add_lengths():
    # Read instances list
    with open(fileio.path("instances list"), newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f, delimiter='\t')
        cable_instances = {
            row["instance_name"].strip(): row["length"]
            for row in reader
            if row.get("item_type", "").strip().lower() == "cable"
        }

    # Read wirelist
    with open(fileio.path("wirelist no formats"), newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f, delimiter='\t')
        wirelist_rows = list(reader)
        original_fieldnames = reader.fieldnames or []

    # Insert "length" between "Wire" and "Subwire"
    if "length" not in original_fieldnames:
        fieldnames = []
        for name in original_fieldnames:
            fieldnames.append(name)
            if name == "Wire":
                fieldnames.append("length")
    else:
        fieldnames = original_fieldnames

    # Update rows with lengths
    for row in wirelist_rows:
        wire_name = row.get("Wire", "").strip()
        if wire_name in cable_instances:
            row["length"] = cable_instances[wire_name]
        else:
            row["length"] = row.get("length", "")

    # Write updated wirelist
    with open(fileio.path("wirelist no formats"), 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter='\t')
        writer.writeheader()
        writer.writerows(wirelist_rows)

    return fileio.path("wirelist no formats")

import xlwt

def tsv_to_xls():
    header_fill_colors = {
        "Wire": "black",
        "Subwire": "black",
        "Source": "green",
        "SourcePin": "green",
        "Destination": "red",
        "DestinationPin": "red",
        "length": "blue"
    }

    header_font_colors = {
        "Wire": "white",
        "Subwire": "white",
        "Source": "white",
        "SourcePin": "white",
        "Destination": "white",
        "DestinationPin": "white",
        "length": "white"
    }

    workbook = xlwt.Workbook()
    sheet = workbook.add_sheet('Sheet1')

    with open(fileio.path("wirelist no formats"), newline='', encoding='utf-8') as tsv_file:
        reader = csv.reader(tsv_file, delimiter='\t')
        headers = next(reader)

        length_col_idx = None
        for col_idx, header in enumerate(headers):
            if header == "length":
                length_col_idx = col_idx

            fill_color = header_fill_colors.get(header)
            font_color = header_font_colors.get(header)

            if fill_color or font_color:
                pattern = f'pattern: pattern solid, fore_color {fill_color};' if fill_color else ''
                font = f'font: bold on, color {font_color};' if font_color else 'font: bold on;'
                style = xlwt.easyxf(f'{font} {pattern}')
            else:
                style = xlwt.easyxf('font: bold on;')

            sheet.write(0, col_idx, header, style)

        # Style for numbers
        number_style = xlwt.XFStyle()
        number_format = xlwt.easyxf(num_format_str='0.00').num_format_str
        number_style.num_format_str = number_format

        for row_idx, row in enumerate(reader, start=1):
            for col_idx, cell in enumerate(row):
                if col_idx == length_col_idx:
                    try:
                        sheet.write(row_idx, col_idx, float(cell), number_style)
                    except ValueError:
                        sheet.write(row_idx, col_idx, cell)  # fallback to string
                else:
                    sheet.write(row_idx, col_idx, cell)

    workbook.save(fileio.path("wirelist formatted"))
