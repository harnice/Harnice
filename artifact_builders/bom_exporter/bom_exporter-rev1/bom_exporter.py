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

output_dir = os.path.join(fileio.dirpath('artifacts'), "bom_exporter")
os.makedirs(output_dir, exist_ok=True)

partnum = fileio.partnumber("pn-rev")
output_tsv_path = os.path.join(output_dir, f"{partnum}-bom.tsv")
output_svg_path = os.path.join(output_dir, f"{partnum}-bom-master.svg")

with open(output_tsv_path, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=BOM_COLUMNS, delimiter='\t')
    writer.writeheader()
    writer.writerows([])

def add_line_to_bom(line_data):
    with open(output_tsv_path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=BOM_COLUMNS, delimiter='\t')
        writer.writerow({key: line_data.get(key, '') for key in BOM_COLUMNS})

highest_bom_number = 0
for instance in instances_list.read_instance_rows():
    if not instance.get("bom_line_number") == "":
        if int(instance.get("bom_line_number")) > highest_bom_number:
            highest_bom_number = int(instance.get("bom_line_number"))

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

# === Create BOM Table SVG ===
selected_columns = ["bom_line_number", "qty", "total_length_exact", "mpn"]
header_labels = ["ITEM", "QTY", "LENGTH", "MPN"]
column_widths = [0.375 * 96, 0.375 * 96, 0.75 * 96, 1.75 * 96]
row_height = 0.16 * 96
font_size = 8
font_family = "Arial, Helvetica, sans-serif"
line_width = 0.008 * 96

with open(output_tsv_path, "r", newline="", encoding="utf-8") as tsv_file:
    reader = csv.DictReader(tsv_file, delimiter="\t")
    data_rows = [
        [row.get(col, "") for col in selected_columns]
        for row in reader
        if row.get("bom_line_number", "").isdigit()
    ]

data_rows.sort(key=lambda r: int(r[0]))
table_rows = data_rows + [header_labels]

num_rows = len(table_rows)
svg_width = sum(column_widths)
svg_height = num_rows * row_height

svg_lines = [
    f'<svg width="{svg_width}" height="{svg_height}" xmlns="http://www.w3.org/2000/svg" '
    f'font-family="{font_family}" font-size="{font_size}">',
    '<g id="bom-contents-start">'
]

column_x_positions = []
running_x = 0
for width in column_widths:
    running_x += width
    column_x_positions.append(-running_x)

for row_index, row in enumerate(reversed(table_rows)):
    y = -1 * (row_index + 1) * row_height
    is_header_row = (row_index == 0)
    rect_fill = "#e0e0e0" if is_header_row else "white"
    font_weight = "bold" if is_header_row else "normal"

    for col_index, cell in enumerate(row):
        x = column_x_positions[col_index]
        cell_width = column_widths[col_index]

        svg_lines.append(
            f'<rect x="{x}" y="{y}" width="{cell_width}" height="{row_height}" '
            f'style="fill:{rect_fill};stroke:black;stroke-width:{line_width}"/>'
        )

        if col_index in (0, 1):
            text_anchor = "middle"
            text_x = x + cell_width / 2
        else:
            text_anchor = "start"
            text_x = x + 5

        text_y = y + row_height / 2
        svg_lines.append(
            f'<text x="{text_x}" y="{text_y}" text-anchor="{text_anchor}" '
            f'style="fill:black;dominant-baseline:middle;font-weight:{font_weight};'
            f'font-family:{font_family};font-size:{font_size}">{cell}</text>'
        )

        if col_index == 0 and not is_header_row:
            circle_cx = x + cell_width / 2
            circle_cy = y + row_height / 2
            radius = min(cell_width, row_height) / 2 - 2

            svg_lines.append(
                f'<circle cx="{circle_cx}" cy="{circle_cy}" r="{radius}" '
                f'style="fill:none;stroke:black;stroke-width:{line_width}"/>'
            )

svg_lines.append('</g>')
svg_lines.append('<g id="bom-contents-end"/>')
svg_lines.append('</svg>')

with open(output_svg_path, "w", encoding="utf-8") as svg_file:
    svg_file.write("\n".join(svg_lines))
