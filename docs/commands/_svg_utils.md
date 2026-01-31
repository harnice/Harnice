# SVG Utilities
---
##Commands:
*Use the following functions by first importing the module in your script like this: 
```python
from harnice.lists import svg_utils
```
 then use as written.*
??? info "`svg_utils.table(layout_dict, format_dict, columns_list, content_list, path_to_svg, contents_group_name)`"

    This function is called when the user needs to build a general SVG table.
    ```python
    svg_utils.table(
        layout_dict,
        format_dict,
        columns_list,
        content_list,
        path_to_caller,
        svg_name
    )
    ```
    ### Arguments
    
    - `layout_dict` expects a dictionary describing in which direction the table is built
    - `format_dict` expects a dictionary containing a description of how you want your table to appear.
    - `columns_list` expects a list containing your column header content, width, and formatting rules.
    - `content_list` expects a list containing what is actually presented on your table.
    
    ### Returns
    
    - A string of SVG primatives in xml format intended to look like a table. 
    
    ---
    
    ## 1. Layout
    
    The SVG origin (0,0) must exist somewhere in your table. Defining this correctly will help later when tables dynamically update with changing inputs. 
    
    *example:*
    ```json
    layout = {
        "origin_corner": "top-left",
        "build_direction": "down",
    }
    ```
    Both fields are required. 
    ### Origin Corner
    
    The origin is defined to be at one of the four corners of the first row `content[0]`. Valid options:
    
    - `top-left`
    - `top-right`
    - `bottom-left`
    - `bottom-right`
    
    ### Build Direction 
    When building a table, you can choose to build rows downwards (below the previous, positive y in svg coords) or upwards (above the previous, negative y in svg coords). The direction property defines this:
    
    - `down` → rows appear below the previous
    - `up` → new rows appear above the previous
    
    ---
    
    ## 2. Format
    
    The format dictionary defines appearance and style of your table. 
    
    Any number of appearance keys can be defined and named with an identifier that is called when printing that row. This allows you to have rows that whose appearance can be varied dynamically with the table contents. 
    
    *example:*
    ```json
    format_dict={
        "globals": {
            "font_size": 11,
            "row_height": 20,
        },
        "header": {
            "font_weight":"B",
            "fill_color": "lightgray",
        },
        "row_with_bubble": {
            "row_height": 40,
        },
    }
    ```
    The only reserved key is `globals` which can optionally be used to define fallbacks for any row that does not have a style explicitly called out.
    
    ### Format Arguments
    Any of the following keys can be defined in any of the format dictionaries. 
    
    - `font_size` *(number, default=12)* Default font size (px) for all text
    - `font_family` *(string, default=helvetica)* Default font family (e.g., "Arial", "Helvetica")
    - `font_weight`*(`BIU`, default=None)* Add each character for bold, italic, or underline
    - `row_height` *(number, default=18)* Self-explanatory (px)
    - `padding` *(number, default=3)* Default text inset from border if not center or middle justified
    - `line_spacing` *(number, default=14)* Vertical spacing between multi-line text entries
    - `justify` *(`left` \ `center` \ `right`, default=center)* Default horizontal alignment
    - `valign` *(`top` \ `middle` \ `bottom`, default=center)* Default vertical alignment
    - `fill_color` *(default=white)* Cell background color
    - `stroke_color` *(default=black)* Border line color
    - `stroke_width` *(number, default=1)* Border width
    - `text_color` *(default=black)* Default text color
    
    ### Style Resolution Order
    If something is defined at the row level, it takes precedent over some parameter defined at the column level, which takes precedent over a definition in key `globals`, if defined. If something is not defined at all, the above defaults will apply. 
    
    ### Color Standard
    
    - Default color: **black**
    - Accepted formats:
    - Named SVG colors https://www.w3.org/TR/SVG11/types.html#ColorKeywords
    - Hex values (#RGB or #RRGGBB)
    
    ---
    
    ## 3. Columns
    
    The column argument is a list of dictionaries containing definition of how many columns there are, the order in which they exist, how to reference them, and any applicable formatting.
    
    *ex:*
    ```json
    columns_list=[
        {
            "name": "rev"
            "width": 60,
            "justify": "center"
        },
        {
            "name": "updated"
            "width": 260,
        },
            "name": "status"
            "width": 120,
            "fill_color": "yellow",
        }
    ]
    ```
    
    ### Column Arguments
    Each field must have the following required keys:
    - `name` *(string)* Used to identify a column when defining contents later. Must be unique.
    - `width` *(number)* Self-explanatory (px)
    
    You may add any formatting key as defined in the formatting section as needed.
    
    Note that the order of the items in the list represents the order in which they will be printed from left to right, regardless of the layout you've chosen for this table.
    
    ---
    
    ## 4. Content Structure
    
    The table content will be referenced from information stored in this argument. It is a list (rows) of dictionaries (columns).
    
    ```json
    content_list = [
        {
            "format_key": "header"
            "columns": {
                "rev": "REV",
                "updated": "UPDATED",
                "status": "STATUS",
            }
        },
        {
            "columns": {
                "rev": "1",
                "updated": "12/6/25",
                "status": "requires review",
            }
        },
        {
            "columns": {
                "rev": "2",
                "updated": ["12/6/25", "update incomplete"],
            }
        },
        {
            "format_key": "row_with_bubble",
            "columns": {
                "rev": {
                    "instance_name": "rev3-bubble",
                    "item_type": "flagnote"
                },
                "updated": "12/6/25",
                "status": "clear"
            }
        }
    ]
    ```
    
    Content (the root argument) is a list. Each entry of the root list is representative of a row's worth of data.
    
    Each entry of that list must contain the dictionary `columns` and may contain dictionary `format_key`. 
    
    `format_key` may only contain one value which corresponds to the name of a key in the format dictionary. It represents the appearance of that row. If it is not defined, the format of that row will fall back to globals and defaults. Custom formatting of individual cells is not supported. 
    
    `columns` is a dictionary that contains the actual content you want to appear in each column. The name of each key at this level must match one of the keys in the `columns` argument. It is agnostic to order, and by leaving a key out, simply nothing will appear in that cell. Existing formatting (cell fill and border) will still apply.
    
    The value of each column key may take one of the following forms:
    - string or number → single-line text, prints directly
    - list[str] → multi-line text where the 0th element prints highest within the cell. Use format key `line_spacing` as needed. 
    - dict → custom 
    
    ### Importing a Symbol into a Cell
    
    If you add a dictionary to one of the content cells, content start/end groups will be written into your svg. This will allow the user to generate and/or import symbols into the table using their own logic, without regard for placement into the table.
    
    ```python
    #from your macro or wherever you're building the table from...
    example_symbol = {
        "lib_repo": instance.get("lib_repo"),
        "item_type": "flagnote",
        "mpn": instance.get("mpn"),
        "instance_name": f"bubble{build_note_number}",
        "note_text": build_note_number,
    }
    symbols_to_build=[example_symbol]
            
    svg_utils.table(
        layout_dict,
        format_dict,
        columns_list,
        content_list,
        os.dirname(path_to_table_svg),
        artifact_id
    )
    
    # user import logic 
    for symbol in symbols_to_build:
        path_to_symbol = #...
        library_utils.pull(
            symbol,
            update_instances_list=False,
            destination_directory=path_to_symbol,
        )
    
        svg_utils.find_and_replace_svg_group(
            os.path.join(path_to_symbol, f"{symbol.get('instance_name')}-drawing.svg"),
            symbol.get("instance_name"),
            path_to_table_svg,
            symbol.get("instance_name")
        )

??? info "`svg_utils.add_entire_svg_file_contents_to_group(filepath, new_group_name)`"

    Wraps the entire contents of an SVG file in a new group element.
    
    Reads an SVG file, extracts its inner content (everything between `<svg>` tags),
    and wraps it in a new group element with start and end markers. The original
    file is modified in place.
    
    **Args:**
    
    - `filepath` (str): Path to the SVG file to modify.
    - `new_group_name` (str): Name to use for the new group element (will create
        `{new_group_name}-contents-start` and `{new_group_name}-contents-end` markers).
    
    **Raises:**
    
    - `ValueError`: If the file does not appear to be a valid SVG or has no inner contents.

??? info "`svg_utils.find_and_replace_svg_group(source_svg_filepath, source_group_name, destination_svg_filepath, destination_group_name)`"

    Copies SVG group content from one file to another, replacing existing group content.
    
    Extracts the content between group markers in a source SVG file and replaces
    the content between corresponding markers in a destination SVG file. The group
    markers are identified by `{group_name}-contents-start` and `{group_name}-contents-end` IDs.
    
    **Args:**
    
    - `source_svg_filepath` (str): Path to the source SVG file containing the group to copy.
    - `source_group_name` (str): Name of the source group to extract content from.
    - `destination_svg_filepath` (str): Path to the destination SVG file to modify.
    - `destination_group_name` (str): Name of the destination group to replace content in.
    
    **Returns:**
    
    - `int`: Always returns `1` (success indicator).
    
    **Raises:**
    
    - `ValueError`: If any of the required group markers are not found in the source
        or destination files.

??? info "`svg_utils.draw_styled_path(spline_points, stroke_width_inches, appearance_dict, local_group)`"

    Adds a styled spline path to the local group.
    Call as if you were appending any other element to an svg group.
    
    Spline points are a list of dictionaries with x and y coordinates. 
    ```python
    [{"x": 0, "y": 0, "tangent": 0}, {"x": 1, "y": 1, "tangent": 0}]
    ```
    
    Appearance dictionary is a dictionary with the following keys: base_color, outline_color, parallelstripe, perpstripe, slash_lines
    ```python
    {
        "base_color": "red",
        "perpstripe": ["orange", "yellow", "green", "blue", "purple"],
    }
    ```
    Slash lines dictionary is a dictionary with the following keys: direction, angle, step, color, slash_width_inches
    ```python
    {
        "direction": "RH",
        "angle": 20,
        "step": 3,
        "color": "black",
        "slash_width_inches": 0.25,
    }
    ```
    
    If no appearance dictionary is provided, a rainbow spline will be drawn in place of the path.

