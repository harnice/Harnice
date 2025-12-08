import os
import re
import math
from harnice.utils import appearance


def add_entire_svg_file_contents_to_group(filepath, new_group_name):
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as file:
                svg_content = file.read()

            match = re.search(r"<svg[^>]*>(.*?)</svg>", svg_content, re.DOTALL)
            if not match:
                raise ValueError(
                    "File does not appear to be a valid SVG or has no inner contents."
                )
            inner_content = match.group(1).strip()

            updated_svg_content = (
                f'<svg xmlns="http://www.w3.org/2000/svg">\n'
                f'  <g id="{new_group_name}-contents-start">\n'
                f"    {inner_content}\n"
                f"  </g>\n"
                f'  <g id="{new_group_name}-contents-end"></g>\n'
                f"</svg>\n"
            )

            with open(filepath, "w", encoding="utf-8") as file:
                file.write(updated_svg_content)

        except Exception as e:
            print(
                f"Error adding contents of {os.path.basename(filepath)} to a new group {new_group_name}: {e}"
            )
    else:
        print(
            f"Trying to add contents of {os.path.basename(filepath)} to a new group but file does not exist."
        )


def find_and_replace_svg_group(
    source_svg_filepath,
    source_group_name,
    destination_svg_filepath,
    destination_group_name,
):
    with open(source_svg_filepath, "r", encoding="utf-8") as source_file:
        source_svg_content = source_file.read()
    with open(destination_svg_filepath, "r", encoding="utf-8") as target_file:
        target_svg_content = target_file.read()

    source_start_tag = f'id="{source_group_name}-contents-start"'
    source_end_tag = f'id="{source_group_name}-contents-end"'
    dest_start_tag = f'id="{destination_group_name}-contents-start"'
    dest_end_tag = f'id="{destination_group_name}-contents-end"'

    source_start_index = source_svg_content.find(source_start_tag)
    if source_start_index == -1:
        raise ValueError(
            f"[ERROR] Source start tag <{source_start_tag}> not found in <{source_svg_filepath}>."
        )
    source_start_index = source_svg_content.find(">", source_start_index) + 1

    source_end_index = source_svg_content.find(source_end_tag)
    if source_end_index == -1:
        raise ValueError(
            f"[ERROR] Source end tag <{source_end_tag}> not found in <{source_svg_filepath}>."
        )
    source_end_index = source_svg_content.rfind("<", 0, source_end_index)

    dest_start_index = target_svg_content.find(dest_start_tag)
    if dest_start_index == -1:
        raise ValueError(
            f"[ERROR] Target start tag <{dest_start_tag}> not found in <{destination_svg_filepath}>."
        )
    dest_start_index = target_svg_content.find(">", dest_start_index) + 1

    dest_end_index = target_svg_content.find(dest_end_tag)
    if dest_end_index == -1:
        raise ValueError(
            f"[ERROR] Target end tag <{dest_end_tag}> not found in <{destination_svg_filepath}>."
        )
    dest_end_index = target_svg_content.rfind("<", 0, dest_end_index)

    replacement_group_content = source_svg_content[source_start_index:source_end_index]

    updated_svg_content = (
        target_svg_content[:dest_start_index]
        + replacement_group_content
        + target_svg_content[dest_end_index:]
    )

    with open(destination_svg_filepath, "w", encoding="utf-8") as updated_file:
        updated_file.write(updated_svg_content)

    return 1


def draw_styled_path(spline_points, stroke_width_inches, appearance_dict, local_group):
    """
    Adds a styled spline path to the local group.
    Call as if you were appending any other element to an svg group.

    Spline points are a list of dictionaries with x and y coordinates. [{"x": 0, "y": 0, "tangent": 0}, {"x": 1, "y": 1, "tangent": 0}]
    Appearance dictionary is a dictionary with the following keys: base_color, outline_color, parallelstripe, perpstripe, slash_lines
    Slash lines dictionary is a dictionary with the following keys: direction, angle, step, color, slash_width_inches

    If no appearance dictionary is provided, a rainbow spline will be drawn in place of the path.
    """

    if not appearance_dict:
        appearance_dict = appearance.parse(
            "{'base_color':'red', 'perpstripe':['orange','yellow','green','blue','purple']}"
        )
        stroke_width_inches = 0.01
    else:
        appearance_dict = appearance.parse(appearance_dict)

    # ---------------------------------------------------------------------
    # --- spline_to_path
    # ---------------------------------------------------------------------
    def spline_to_path(points):
        if len(points) < 2:
            return ""
        path = f"M {points[0]['x']:.3f},{-points[0]['y']:.3f}"
        for i in range(len(points) - 1):
            p0, p1 = points[i], points[i + 1]
            t0, t1 = math.radians(p0.get("tangent", 0)), math.radians(
                p1.get("tangent", 0)
            )
            d = math.hypot(p1["x"] - p0["x"], p1["y"] - p0["y"])
            ctrl_dist = d * 0.5
            c1x = p0["x"] + math.cos(t0) * ctrl_dist
            c1y = p0["y"] + math.sin(t0) * ctrl_dist
            c2x = p1["x"] - math.cos(t1) * ctrl_dist
            c2y = p1["y"] - math.sin(t1) * ctrl_dist
            path += f" C {c1x:.3f},{-c1y:.3f} {c2x:.3f},{-c2y:.3f} {p1['x']:.3f},{-p1['y']:.3f}"
        return path

    # ---------------------------------------------------------------------
    # --- draw consistent slanted hatches (twisted wire)
    # ---------------------------------------------------------------------
    def draw_slash_lines(points, slash_lines_dict):
        if slash_lines_dict.get("direction") in ("RH", "LH"):
            if slash_lines_dict.get("angle") is not None:
                angle_slant = slash_lines_dict.get("angle")
            else:
                angle_slant = 20
            if slash_lines_dict.get("step") is not None:
                step_dist = slash_lines_dict.get("step")
            else:
                step_dist = stroke_width * 3
            if slash_lines_dict.get("color") is not None:
                color_line = slash_lines_dict.get("color")
            else:
                color_line = "black"
            if slash_lines_dict.get("color") is not None:
                color_line = slash_lines_dict.get("color")
            else:
                color_line = "black"
            if slash_lines_dict.get("slash_width_inches") is not None:
                slash_width = slash_lines_dict.get("slash_width_inches") * 96
            else:
                slash_width = 0.25

        line_elements = []

        def bezier_eval(p0, c1, c2, p1, t):
            mt = 1 - t
            x = (
                (mt**3) * p0[0]
                + 3 * (mt**2) * t * c1[0]
                + 3 * mt * (t**2) * c2[0]
                + (t**3) * p1[0]
            )
            y = (
                (mt**3) * p0[1]
                + 3 * (mt**2) * t * c1[1]
                + 3 * mt * (t**2) * c2[1]
                + (t**3) * p1[1]
            )
            dx = (
                3 * (mt**2) * (c1[0] - p0[0])
                + 6 * mt * t * (c2[0] - c1[0])
                + 3 * (t**2) * (p1[0] - c2[0])
            )
            dy = (
                3 * (mt**2) * (c1[1] - p0[1])
                + 6 * mt * t * (c2[1] - c1[1])
                + 3 * (t**2) * (p1[1] - c2[1])
            )
            return {"x": x, "y": y, "tangent": math.degrees(math.atan2(dy, dx))}

        def bezier_length(p0, c1, c2, p1, samples=80):
            prev = bezier_eval(p0, c1, c2, p1, 0)
            L = 0.0
            for i in range(1, samples + 1):
                t = i / samples
                pt = bezier_eval(p0, c1, c2, p1, t)
                L += math.hypot(pt["x"] - prev["x"], pt["y"] - prev["y"])
                prev = pt
            return L

        # -------------------------------------------------------------
        # Iterate through Bézier segments
        for i in range(len(points) - 1):
            p0 = (points[i]["x"], points[i]["y"])
            p1 = (points[i + 1]["x"], points[i + 1]["y"])
            t0 = math.radians(points[i].get("tangent", 0))
            t1 = math.radians(points[i + 1].get("tangent", 0))
            d = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
            ctrl_dist = d * 0.5
            c1 = (p0[0] + math.cos(t0) * ctrl_dist, p0[1] + math.sin(t0) * ctrl_dist)
            c2 = (p1[0] - math.cos(t1) * ctrl_dist, p1[1] - math.sin(t1) * ctrl_dist)

            L = bezier_length(p0, c1, c2, p1)
            num_steps = max(1, int(L / step_dist))
            step_dist_actual = L / num_steps  # uniform spacing

            for z in range(num_steps + 1):
                # ------------------------------------------------------------------
                # 1. Evaluate point along Bézier curve
                # ------------------------------------------------------------------
                t_norm = min(1.0, (z * step_dist_actual) / L)
                P = bezier_eval(p0, c1, c2, p1, t_norm)

                # Centerpoint on spline
                center = (P["x"], P["y"])

                # ------------------------------------------------------------------
                # 2. Tangent and hatch angle computation
                # ------------------------------------------------------------------
                # Tangent direction of the spline at this point (radians)
                tangent_angle = math.radians(P["tangent"])

                # LH vs RH determines whether we add or subtract the slant
                if slash_lines_dict.get("direction") == "LH":
                    line_angle = tangent_angle + math.radians(angle_slant)
                else:  # "RH"
                    line_angle = tangent_angle - math.radians(angle_slant)

                # ------------------------------------------------------------------
                # 3. Compute hatch line geometry
                # ------------------------------------------------------------------
                # Shorter lines at steep slant; normalize by cos(slant)
                line_length = stroke_width / math.sin(math.radians(angle_slant))

                # Vector along hatch direction
                dx = math.cos(line_angle) * (line_length / 2)
                dy = math.sin(line_angle) * (line_length / 2)

                # Line endpoints
                x1 = center[0] - dx
                y1 = center[1] - dy
                x2 = center[0] + dx
                y2 = center[1] + dy

                # ------------------------------------------------------------------
                # 4. Append SVG element
                # ------------------------------------------------------------------
                line_elements.append(
                    f'<line x1="{x1:.2f}" y1="{-y1:.2f}" '
                    f'x2="{x2:.2f}" y2="{-y2:.2f}" '
                    f'stroke="{color_line}" stroke-width="{slash_width}" />'
                )

        local_group.extend(line_elements)

    # ---------------------------------------------------------------------
    # --- Main body rendering
    # ---------------------------------------------------------------------
    base_color = appearance_dict.get("base_color", "white")
    outline_color = appearance_dict.get("outline_color")
    path_d = spline_to_path(spline_points)

    # outline path
    stroke_width = stroke_width_inches * 96
    if outline_color:
        local_group.append(
            f'<path d="{path_d}" stroke="{outline_color}" stroke-width="{stroke_width}" '
            f'fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
        )
        stroke_width = stroke_width - 0.5

    # base path
    local_group.append(
        f'<path d="{path_d}" stroke="{base_color}" stroke-width="{stroke_width}" '
        f'fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
    )

    # ---------------------------------------------------------------------
    # --- Add pattern overlays
    # ---------------------------------------------------------------------
    if appearance_dict.get("parallelstripe"):
        stripes = appearance_dict["parallelstripe"]
        num = len(stripes)
        stripe_thickness = stroke_width / num
        stripe_spacing = stroke_width / num
        offset = -(num - 1) * stripe_spacing / 2
        for color in stripes:
            local_group.append(
                f'<path d="{path_d}" stroke="{color}" '
                f'stroke-width="{stripe_thickness}" fill="none" '
                f'transform="translate(0,{offset:.2f})"/>'
            )
            offset += stripe_spacing

    if appearance_dict.get("perpstripe"):
        stripes = appearance_dict["perpstripe"]
        num = len(stripes)
        pattern_length = 30
        dash = pattern_length / (num + 1)
        gap = pattern_length - dash
        offset = 0
        for color in stripes:
            offset += dash
            local_group.append(
                f'<path d="{path_d}" stroke="{color}" stroke-width="{stroke_width}" '
                f'stroke-dasharray="{dash},{gap}" stroke-dashoffset="{offset}" '
                f'fill="none" />'
            )

    # --- Slash lines ---
    if appearance_dict.get("slash_lines") is not None:
        slash_lines_dict = appearance_dict.get("slash_lines")
        draw_slash_lines(spline_points, slash_lines_dict)


# --- Default Style Values (Required for the class) ---
DEFAULTS = {
    "font_size": 12,
    "font_family": "helvetica",
    "font_weight": None,
    "row_height": 18,
    "padding": 3,
    "line_spacing": 14,
    "justify": "center",
    "valign": "middle",
    "fill_color": "white",
    "stroke_color": "black",
    "stroke_width": 1,
    "text_color": "black",
}

class SvgTableGenerator:
    """
    Generates an SVG table based on Harnice Table Requirements (rev2).
    """
    def __init__(self, layout_dict, format_dict, columns_list, content_list, path_to_caller, svg_name):
        self.layout = self._validate_layout(layout_dict)
        self.format = format_dict
        self.columns = self._validate_columns(columns_list)
        self.content = content_list
        self.total_width = sum(col['width'] for col in self.columns)

    def _validate_layout(self, layout):
        """Validates the layout dictionary."""
        valid_corners = {"top-left", "top-right", "bottom-left", "bottom-right"}
        valid_directions = {"down", "up"}
        
        corner = layout.get("origin_corner")
        direction = layout.get("build_direction")

        if corner not in valid_corners:
            raise ValueError(f"Invalid origin_corner: {corner}. Must be one of {valid_corners}.")
        if direction not in valid_directions:
            raise ValueError(f"Invalid build_direction: {direction}. Must be one of {valid_directions}.")
            
        return layout

    def _validate_columns(self, columns_list):
        """Validates the columns list, ensuring 'name' and 'width' are present."""
        if not columns_list:
            raise ValueError("columns_list cannot be empty.")
        names = set()
        for col in columns_list:
            if 'name' not in col or 'width' not in col:
                raise ValueError("Each column must have 'name' and 'width' keys.")
            if col['name'] in names:
                raise ValueError(f"Duplicate column name: {col['name']}.")
            names.add(col['name'])
        return columns_list
    
    def _resolve_style(self, row_format_key, col_data):
        """
        Resolves the final style for a cell following the Style Resolution Order:
        Row Format > Column Format > Globals > Defaults.
        """
        style = DEFAULTS.copy()

        # 1. Globals
        style.update(self.format.get("globals", {}))
        
        # 2. Column Format
        col_name = col_data.get('name')
        column_def = next((c for c in self.columns if c['name'] == col_name), {})
        style.update({k: v for k, v in column_def.items() if k in DEFAULTS})

        # 3. Row Format
        row_format = self.format.get(row_format_key)
        if row_format:
            style.update({k: v for k, v in row_format.items() if k in DEFAULTS})
            
        return style

    def _generate_symbol_placeholder(self, instance_name, bubble_x, bubble_y):
        """
        Generates the SVG group structure used as a placeholder for external tools 
        to inject drawing content based on instance_name and start/end markers.
        """
        svg_lines = []
        
        svg_lines.append(
            f'<g id="{instance_name}" transform="translate({bubble_x},{bubble_y})">'
        )
        # Content Start marker
        svg_lines.append(f'  <g id="{instance_name}-contents-start">')
        svg_lines.append(f"  </g>")
        
        # Content End marker (using the self-closing tag format)
        svg_lines.append(f'  <g id="{instance_name}-contents-end"/>')
        
        svg_lines.append(f"</g>")
        
        return "\n".join(svg_lines)

    def _draw_cell_content(self, x, y, width, height, content, style):
        """
        Generates the SVG for the cell's content (text or symbol).
        """
        svg_primitives = []
        instances_to_copy_in = []
        
        # --- Handle Content Type ---
        if isinstance(content, dict) and 'instance_name' in content:
            # 1. Importing a Symbol (Placeholder Generation)
            instance_name = content['instance_name']
            item_type = content['item_type']
            
            # --- Symbol Positioning (Alignment) ---
            align_x = 0
            if style['justify'] == 'center':
                align_x = width / 2
            elif style['justify'] == 'right':
                align_x = width - style['padding']
            elif style['justify'] == 'left':
                align_x = style['padding']
                
            align_y = 0
            if style['valign'] == 'middle':
                align_y = height / 2
            elif style['valign'] == 'bottom':
                align_y = height - style['padding']
            elif style['valign'] == 'top':
                align_y = style['padding']

            # Call the integrated method to generate the required placeholder structure
            # The symbol's local origin (0,0) is placed at the calculated alignment point.
            symbol_xml = self._generate_symbol_placeholder(
                instance_name=instance_name,
                bubble_x=x + align_x,
                bubble_y=y + align_y
            )
            instances_to_copy_in.append({"item_type":item_type, "instance_name":instance_name})
            svg_primitives.append(symbol_xml)

        else:
            # 2. Text Content (string, number, or list of strings)
            text_lines = []
            if isinstance(content, (str, int, float)):
                text_lines = [str(content)]
            elif isinstance(content, list):
                text_lines = [str(line) for line in content]
            
            if not text_lines:
                return ""

            # --- Text Positioning Logic ---
            x_pos = x
            text_anchor = "start"
            # ... (rest of text positioning logic remains the same)
            if style['justify'] == 'center':
                x_pos += width / 2
                text_anchor = "middle"
            elif style['justify'] == 'right':
                x_pos += width - style['padding']
                text_anchor = "end"
            elif style['justify'] == 'left':
                x_pos += style['padding']
                text_anchor = "start"

            num_lines = len(text_lines)
            total_text_height = (num_lines - 1) * style['line_spacing'] + style['font_size']
            
            y_start = y
            if style['valign'] == 'middle':
                y_start += (height - total_text_height) / 2
            elif style['valign'] == 'bottom':
                y_start += height - total_text_height - style['padding']
            elif style['valign'] == 'top':
                y_start += style['padding']
            
            y_pos = y_start + style['font_size'] * 0.8 

            # --- Text Style Attributes ---
            text_style = {
                "font-size": f"{style['font_size']}px",
                "font-family": style['font_family'],
                "fill": style['text_color'],
                "text-anchor": text_anchor,
            }
            # ... (font weight logic remains the same)
            if style['font_weight']:
                if 'B' in style['font_weight']:
                    text_style['font-weight'] = 'bold'
                if 'I' in style['font_weight']:
                    text_style['font-style'] = 'italic'
                if 'U' in style['font_weight']:
                    text_style['text-decoration'] = 'underline'
            
            style_str = "; ".join(f"{k}: {v}" for k, v in text_style.items())

            # --- Generate Text SVG ---
            for i, line in enumerate(text_lines):
                current_y = y_pos + i * style['line_spacing']
                svg_primitives.append(
                    f'<text x="{x_pos}" y="{current_y}" style="{style_str}">{line}</text>'
                )

        return "\n".join(svg_primitives), instances_to_copy_in

    def _draw_cell_rect(self, x, y, width, height, style):
        """
        Generates the SVG for the cell's background and border.
        """
        rect_style = {
            "fill": style['fill_color'],
            "stroke": style['stroke_color'],
            "stroke-width": style['stroke_width'],
        }
        style_str = "; ".join(f"{k}: {v}" for k, v in rect_style.items())
        
        return f'<rect x="{x}" y="{y}" width="{width}" height="{height}" style="{style_str}" />'

    def build_svg(self, path_to_caller, svg_name):
        """
        Main function to iterate through content and build the complete SVG string,
        returning only the group (<g>) element with primitives inside.
        """
        svg_rows = []
        col_x_starts = [0]
        current_x = 0
        for col in self.columns[:-1]:
            current_x += col['width']
            col_x_starts.append(current_x)

        # Calculate total table height and individual row heights
        row_heights = [
            self._resolve_style(row.get('format_key'), {}).get('row_height', DEFAULTS['row_height'])
            for row in self.content
        ]
        total_table_height = sum(row_heights)
        row_height_0 = row_heights[0]
        
        current_y_offset = 0 

        instances_to_copy_in = []

        print("!!!!!!! 570")
        
        # --- Build Row by Row ---
        for row_index, row_data in enumerate(self.content):
            row_key = row_data.get('format_key')
            row_height = row_heights[row_index]
            
            row_svg = []
            
            # --- Y Position Logic ---
            if self.layout['build_direction'] == 'down':
                cell_y_start = current_y_offset
                current_y_offset += row_height
            
            elif self.layout['build_direction'] == 'up':
                current_y_offset -= row_height
                cell_y_start = current_y_offset

            # --- Column Iteration ---
            for col_index, col_def in enumerate(self.columns):
                col_name = col_def['name']
                col_width = col_def['width']
                cell_content = row_data.get('columns', {}).get(col_name)
                
                cell_style = self._resolve_style(row_key, col_def)
                
                cell_x_start = col_x_starts[col_index]
                
                # 1. Draw Cell Rectangle (Background/Border)
                rect_svg = self._draw_cell_rect(cell_x_start, cell_y_start, col_width, row_height, cell_style)
                row_svg.append(rect_svg)
                
                # 2. Draw Cell Content
                if cell_content is not None:
                    content_svg, instances = self._draw_cell_content(
                        cell_x_start, cell_y_start, col_width, row_height, 
                        cell_content, cell_style
                    )
                    row_svg.append(content_svg)
                    instances_to_copy_in.extend(instances)

            svg_rows.append("\n".join(row_svg))
            
        # --- Calculate Final Table Transform (Positioning (0,0) at Origin Corner) ---
        
        tx = 0
        ty = 0
        
        # X Translation
        if self.layout['origin_corner'] in ('top-right', 'bottom-right'):
            tx = -self.total_width
        
        # Y Translation: Ensures the first row's required corner is at Y=0
        if self.layout['build_direction'] == 'down':
            if self.layout['origin_corner'] in ('bottom-left', 'bottom-right'):
                ty = -row_height_0

        elif self.layout['build_direction'] == 'up':
            if self.layout['origin_corner'] in ('top-left', 'top-right'):
                ty = total_table_height
            
        table_contents = "\n".join(svg_rows)

        # RETURN ONLY THE <g> ELEMENT AND ITS CONTENTS
        group_output = f"""<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="1000">
  <g id="{svg_name}-contents-start">
    <g id="translate" transform="translate({tx}, {ty})">
{table_contents}
    </g>
  <g id="{svg_name}-contents-end">
</svg>"""

        print("!!!!!!!640")

        path_to_svg = os.path.join(path_to_caller, f"{svg_name}-master.svg")
        with open(path_to_svg, "w") as f:
            f.write(group_output.strip())

        for instance in instances_to_copy_in:
            find_and_replace_svg_group(
                os.path.join(path_to_caller, "instance_data", instance.get("item_type"), instance.get("instance_name")),
                instance.get("instance_name"),
                path_to_svg,
                svg_name
            )
        
        return group_output.strip()


# ====================================================================
# The required function signature
# ====================================================================

def table(layout_dict, format_dict, columns_list, content_list, path_to_caller, svg_name):
    """
    
    Arguments:
    - layout_dict (dict): Defines origin and build direction.
    - format_dict (dict): Defines global and row-specific appearance styles.
    - columns_list (list): Defines column headers, widths, and column styles.
    - content_list (list): The actual table data, including cell content and row format keys.

    Returns:
    - A string of SVG primitives in xml format.
    """
    try:
        print("!!!!!676")
        SvgTableGenerator(layout_dict, format_dict, columns_list, content_list, path_to_caller, svg_name)
    except ValueError as e:
        # In a real utility, this would likely log the error or return a minimal 
        # error SVG. For this function, we'll raise the error.
        raise RuntimeError(f"Failed to generate table due to input error: {e}")