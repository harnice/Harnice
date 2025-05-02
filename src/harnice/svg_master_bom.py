import csv
import fileio

def prep_bom_svg_master():
    # === Config ===
    selected_columns = ["bom_line_number", "qty", "total_length_exact", "mpn"]
    header_labels = ["ITEM", "QTY", "LENGTH", "MPN"]
    column_widths = [0.375 * 96, 0.375 * 96, 0.75 * 96, 1.75 * 96]  # in pixels
    row_height = 0.16 * 96
    font_size = 8
    font_family = "Arial"
    line_width = 0.008 * 96

    # === Read TSV Data ===
    with open(fileio.path("harness bom"), "r", newline="", encoding="utf-8") as tsv_file:
        reader = csv.DictReader(tsv_file, delimiter="\t")
        data_rows = [
            [row.get(col, "") for col in selected_columns]
            for row in reader
            if row.get("bom_line_number", "").isdigit()
        ]

    # Sort by bom_line_number numerically
    data_rows.sort(key=lambda r: int(r[0]))

    # Add header row last (to appear at bottom when flipped)
    table_rows = data_rows + [header_labels]

    num_rows = len(table_rows)
    svg_width = sum(column_widths)
    svg_height = num_rows * row_height

    # === Begin SVG Output ===
    svg_lines = [
        f'<svg width="{svg_width}" height="{svg_height}" font-family="{font_family}" font-size="{font_size}">',
        f'<g id="bom-master-contents-start" transform="translate({-1 * svg_width}, {-1 * svg_height})">'
    ]

    for row_index, row in enumerate(reversed(table_rows)):
        y = row_index * row_height
        for col_index, cell in enumerate(row):
            x = sum(column_widths[:col_index])
            cell_width = column_widths[col_index]

            # Cell background
            svg_lines.append(
                f'<rect x="{x}" y="{y}" width="{cell_width}" height="{row_height}" '
                f'fill="white" stroke="black" stroke-width="{line_width}"/>'
            )

            # Text alignment
            if col_index in (0, 1):  # center-aligned
                text_anchor = "middle"
                text_x = x + cell_width / 2
            else:  # left-aligned
                text_anchor = "start"
                text_x = x + 5

            text_y = y + row_height / 2
            svg_lines.append(
                f'<text x="{text_x}" y="{text_y}" fill="black" '
                f'text-anchor="{text_anchor}" dominant-baseline="middle">{cell}</text>'
            )

            if (col_index == 0): # Determine if the current column is the "ITEM" column
                if (row_index != 0): # Determine if the current row is not the header row
                    circle_cx = x + cell_width / 2
                    circle_cy = y + row_height / 2
                    radius = min(cell_width, row_height) / 2 - 2

                    svg_lines.append(
                        f'<circle cx="{circle_cx}" cy="{circle_cy}" r="{radius}" '
                        f'fill="none" stroke="black" stroke-width="{line_width}"/>'
                    )

    svg_lines.append('</g>')
    svg_lines.append('<g id="bom-master-contents-end"></g>')
    svg_lines.append('</svg>')

    # === Write SVG Output ===
    with open(fileio.path("bom table master svg"), "w", encoding="utf-8") as svg_file:
        svg_file.write("\n".join(svg_lines))

if __name__ == "__main__":
    prep_bom_svg_master()
