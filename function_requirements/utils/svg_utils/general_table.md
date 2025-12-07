# 📝 Harnice Table Requirements (rev2)

This function is called when the user needs to build a general SVG table.
```python
svg_utils.table(layout_dict, format_dict, columns_list, content_list)
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

If you add a dictionary to one of the content cells with key `instance_name`, the function will add a drawing to the cell.
 - First the current macro's `instances` folder will be searched for a file with name `*-drawing.svg`. That file will be searched for contents between `*-contents-start` and `*-contents-end` (where `*` represents the same string of characters defined in `instance-name` of the data cell).
 - The svg text in between will be copied and pasted into the cell of your column.
 - If that drawing does not exist, or if either start or end tags are not found, the function will fail. It is up to the user to ensure the drawing exists before calling this function.
 - Local table formatting will not apply to the imported drawing
 - The drawing origin will obey the same justification rules as the text, and there is no boundary or clipping logic applied to the imported svg.

---

End of Requirements — rev2

# Issues

[ ] `"font_color"="white"` seems to not be working
[x] y coords of all elements off during `"build_direction"="up"`, was ok before b24ee7d05838ca2f4e232828cf0afebed68b1b5c
