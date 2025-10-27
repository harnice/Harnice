import csv
import os
import yaml
import xlwt
from harnice import fileio, instances_list

artifact_mpn = "wirelist_exporter"


# =============== PATHS ===============
def file_structure():
    return {
        "instance_data": {
            "imported_instances": {
                "macro": {
                    artifact_id: {
                        f"{fileio.partnumber('pn-rev')}-{artifact_id}-wirelist.tsv": "wirelist no formats",
                        f"{fileio.partnumber('pn-rev')}-{artifact_id}-wirelist.xls": "wirelist pretty",
                        f"{fileio.partnumber('pn-rev')}-{artifact_id}-wirelist-master.svg": "wirelist svg",
                    }
                }
            }
        }
    }


# =============== WIRELIST COLUMNS ===============
WIRELIST_COLUMNS = [
    {"name": "circuit_id", "fill": "black", "font": "white"},
    {"name": "Length", "fill": "black", "font": "white"},
    {"name": "cable", "fill": "black", "font": "white"},
    {"name": "Conductor_identifier", "fill": "black", "font": "white"},
    {"name": "From_connector", "fill": "green", "font": "white"},
    {"name": "From_connector_cavity", "fill": "green", "font": "white"},
    {"name": "From_special_contact", "fill": "green", "font": "white"},
    {"name": "To_special_contact", "fill": "red", "font": "white"},
    {"name": "To_connector", "fill": "red", "font": "white"},
    {"name": "To_connector_cavity", "fill": "red", "font": "white"},
]

# =============== CREATE TSV ===============
with open(
    fileio.path("wirelist no formats", structure_dict=file_structure()), "w", newline=""
) as file:
    writer = csv.writer(file, delimiter="\t")
    writer.writerow([col["name"] for col in WIRELIST_COLUMNS])

column_names = [col["name"] for col in WIRELIST_COLUMNS]


def add(row_data):
    with open(
        fileio.path("wirelist no formats", structure_dict=file_structure()),
        "a",
        newline="",
        encoding="utf-8",
    ) as f:
        writer = csv.DictWriter(f, fieldnames=column_names, delimiter="\t")
        writer.writerow({key: row_data.get(key, "") for key in column_names})


# =============== POPULATE TSV ===============
for instance in fileio.read_tsv("instances list"):
    if instance.get("item_type") != "circuit":
        continue

    circuit_id = instance.get("instance_name")
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
    for instance3 in fileio.read_tsv("instances list"):
        if (
            instance3.get("circuit_id") == circuit_id
            and instance3.get("item_type") == "connector cavity"
        ):
            if connector_cavity_counter == 0:
                from_connector_cavity = instance3.get("instance_name")
                from_connector = instances_list.attribute_of(
                    from_connector_cavity, "parent_instance"
                )
            elif connector_cavity_counter == 1:
                to_connector_cavity = instance3.get("instance_name")
                to_connector = instances_list.attribute_of(
                    to_connector_cavity, "parent_instance"
                )
            else:
                raise ValueError(
                    f"There are 3 or more cavities specified in circuit {circuit_id} "
                    "but expected two (to, from) when building wirelist."
                )
            connector_cavity_counter += 1

    # Locate special contacts
    for instance4 in fileio.read_tsv("instances list"):
        if (
            instance4.get("circuit_id") == circuit_id
            and instance4.get("item_type") == "Contact"
        ):
            parent = instance4.get("parent_instance")
            if parent == from_connector:
                from_special_contact = instance4.get("instance_name")
            elif parent == to_connector:
                to_special_contact = instance4.get("instance_name")

    # Locate conductor
    for instance5 in fileio.read_tsv("instances list"):
        if (
            instance5.get("circuit_id") == circuit_id
            and instance5.get("item_type") == "Conductor"
        ):
            conductor_identifier = instance5.get("print_name")
            cable = instance5.get("parent_instance")
            length = instance5.get("length")

    add(
        {
            "circuit_id": circuit_id,
            "Length": length,
            "cable": cable,
            "Conductor_identifier": conductor_identifier,
            "From_connector": instances_list.attribute_of(from_connector, "print_name"),
            "From_connector_cavity": instances_list.attribute_of(
                from_connector_cavity, "print_name"
            ),
            "From_special_contact": from_special_contact,
            "To_special_contact": to_special_contact,
            "To_connector": instances_list.attribute_of(to_connector, "print_name"),
            "To_connector_cavity": instances_list.attribute_of(
                to_connector_cavity, "print_name"
            ),
        }
    )

# =============== CONVERT TSV TO XLS ===============
workbook = xlwt.Workbook()
sheet = workbook.add_sheet("Sheet1")

with open(
    fileio.path("wirelist no formats", structure_dict=file_structure()),
    newline="",
    encoding="utf-8",
) as tsv_file:
    reader = csv.reader(tsv_file, delimiter="\t")
    headers = next(reader)

    expected_headers = [col["name"] for col in WIRELIST_COLUMNS]
    if headers != expected_headers:
        print("Warning: header mismatch between file and WIRELIST_COLUMNS")

    length_col_idx = None
    for col_idx, header in enumerate(headers):
        if header == "Length (in)":
            length_col_idx = col_idx

        col_config = next(
            (col for col in WIRELIST_COLUMNS if col["name"] == header), {}
        )
        fill_color = col_config.get("fill")
        font_color = col_config.get("font")

        pattern = (
            f"pattern: pattern solid, fore_color {fill_color};" if fill_color else ""
        )
        font = f"font: bold on, color {font_color};" if font_color else "font: bold on;"
        style = xlwt.easyxf(f"{font} {pattern}")
        sheet.write(0, col_idx, header, style)

    number_style = xlwt.XFStyle()
    number_format = xlwt.easyxf(num_format_str="0.00").num_format_str
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

workbook.save(fileio.path("wirelist pretty", structure_dict=file_structure()))

# =============== CREATE SVG ===============
col_width = 76
row_height = 12
font_size = 8
font_family = "Arial"
start_x = 0
start_y = 0

with open(
    fileio.path("wirelist no formats", structure_dict=file_structure()),
    "r",
    encoding="utf-8",
) as f:
    reader = csv.DictReader(f, delimiter="\t")
    data_rows = list(reader)

svg_lines = [
    f"""<?xml version="1.0" encoding="UTF-8" standalone="no"?>
        <svg xmlns="http://www.w3.org/2000/svg" version="1.1">
        <g id="{artifact_id}-wirelist-contents-start">"""
]

for col_idx, col in enumerate(WIRELIST_COLUMNS):
    x = start_x + col_idx * col_width
    y = start_y
    svg_lines.append(
        f"""
<rect x="{x}" y="{y}" width="{col_width}" height="{row_height}" fill="{col["fill"]}" stroke="black" />
<text x="{x + col_width / 2}" y="{y + row_height / 2}" fill="{col["font"]}" text-anchor="middle" dominant-baseline="middle" font-family="{font_family}" font-size="{font_size}">{col["name"]}</text>"""
    )

for row_idx, row in enumerate(data_rows):
    y = start_y + (row_idx + 1) * row_height
    for col_idx, col in enumerate(WIRELIST_COLUMNS):
        x = start_x + col_idx * col_width
        text = row.get(col["name"], "")
        svg_lines.append(
            f"""
<rect x="{x}" y="{y}" width="{col_width}" height="{row_height}" fill="white" stroke="black" />
<text x="{x + col_width / 2}" y="{y + row_height / 2}" fill="black" text-anchor="middle" dominant-baseline="middle" font-family="{font_family}" font-size="{font_size}">{text}</text>"""
        )

svg_lines.append("</g>")
svg_lines.append(f'<g id="{artifact_id}-wirelist-contents-end"/>')
svg_lines.append("</svg>")

with open(
    fileio.path("wirelist svg", structure_dict=file_structure()), "w", encoding="utf-8"
) as f:
    f.write("\n".join(svg_lines))
