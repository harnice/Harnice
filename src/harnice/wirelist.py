import csv
import os
import yaml
import xlwt
from os.path import basename
from inspect import currentframe
from harnice import (
    fileio
)

WIRELIST_COLUMNS = []

def newlist(wirelist_columns_input):
    global WIRELIST_COLUMNS
    WIRELIST_COLUMNS = wirelist_columns_input
    with open(fileio.path("wirelist no formats"), 'w', newline='') as file:
        writer = csv.writer(file, delimiter='\t')
        writer.writerow([col["name"] for col in WIRELIST_COLUMNS])
        writer.writerows([])

def add(row_data):
    column_names = [col["name"] for col in WIRELIST_COLUMNS]
    with open(fileio.path('wirelist no formats'), 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=column_names, delimiter='\t')
        writer.writerow({key: row_data.get(key, '') for key in column_names})

def tsv_to_xls():
    workbook = xlwt.Workbook()
    sheet = workbook.add_sheet('Sheet1')

    with open(fileio.path("wirelist no formats"), newline='', encoding='utf-8') as tsv_file:
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

    workbook.save(fileio.path("wirelist formatted"))