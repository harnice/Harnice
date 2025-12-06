# 📝 Harnice Table Requirements (rev2)

This function is called when the user needs to build a general SVG table.
```python
svg_utils.table(layout, format, columns, content)
```
### Arguments
- `layout` expects a dictionary describing in which direction the table is built
- `format` expects a dictionary containing a description of how you want your table to appear.
- `columns` expects a list containing your column header content, width, and formatting rules.
- `content` expects a list containing what is actually presented on your table.

### Returns
- A string of SVG content intended to look like a table

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

The origin is defined to be at one of the four corners of the header row, and the table content rows are either built above or below.

Valid header anchor points:
- `top-left`
- `top-right`
- `bottom-left`
- `bottom-right`

### Build Direction 
When building a table, you can choose the header to be at the top and the content rows to build downwards (positive y in svg coords) or the header can be at the bottom and the rows build upwards (negative y in svg coords). 

The direction property determines where content rows are placed relative to the header:
- `up` → rows appear above the header
- `down` → rows appear below the header

---

## 2. Format

The format dictionary defines appearance, structure, layout, and style behavior. 

Each key (except `globals`, the only reserved key) describes the format of the entire row that uses that format. 

*example:*
```json
format={
    "globals": {
        "font_size": 11,
        "row_height": 20,
    },
    "header": {
        "font_weight":"B",
        "fill_color": "lightgray",
    },
    "row_standard": {
        "row_height": 20,
    },
    "row_with_bubble": {
        "row_height": 40,
    },
}
```

### Format Arguments
Any key can be defined in any of the format dictionaries. On the backend, "globals" is rewritten with the below defaults if they are not defined in your argument.
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

### Style resolution order
If something is defined at the row level, it takes precedent over a column definition, which takes precedent over a definition in key `globals`, if defined.

---

## 3. Columns

The column argument is a list of dictionaries containing definition of how many columns there are, the order in which they exist, how to reference them, and any applicable formatting.

*ex:*
```json
columns=[
    {
        "name": "rev"
        "width": 60,
        "justify": "center"
    },
    {
        "name": "update"
        "width": 260,
    },
        "name": "status"
        "width": 120,
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

Content is a list of row dictionaries.

```python
content = [{"row_format": "<row_format_id>", "columns": {...}}]
```

**Allowed cell data types:**
- string or number → single-line text
- list[str] → multi-line text (explicit line breaks used)
- dict → symbol placeholder (`<g>` inject target)

One content type per cell.

---

## 5. Justification Rules

**Horizontal options:**
- left
- center
- right

**Vertical options:**
- top
- middle
- bottom

**Rules:**
- **Center alignment ignores padding.**
- **Non-centered alignment uses padding offsets.**
- Lists and symbol placeholders follow the same alignment behavior.

Default padding = globals unless overridden by row format.

---

## 6. Color Specification

- Default color: **black**
- Accepted formats:
  - Named SVG colors
  - Hex values (#RGB or #RRGGBB)

Reference Named Colors: https://www.w3.org/TR/SVG11/types.html#ColorKeywords

---

## 7. Rendering Behavior

Rendering respects:
- Header anchor position
- Build direction
- Column widths
- Row heights

Each cell renders:
1. A bounding rectangle
2. A text element or symbol placeholder

---

## 8. Output Specification

The function returns a complete SVG `<g>` block as a string.

**Example:**

`"<g> ... </g>"`

---

## Example Usage (reference only)

```python
svg_table(
    format={
        "globals": {"font_size": 10, "padding": 4},
        "header_format": {
            "row_height": 22,
            "font_size": 12,
            "fill": "lightgray",
            "justify": "center",
        },
        "row_standard": {"row_height": 18},
        "row_with_bubble": {"row_height": 32, "fill": "#e6f2ff"},
        "columns": {
            "rev": {"name": "rev", "width": 60, "justify": "center"},
            "update": {"name": "update", "width": 260, "justify": "left"},
            "status": {"name": "status", "width": 120, "justify": "center"},
        },
        "origin_corner": "top-left",
        "direction": "down",
    },
    content=[
        {
            "row_format": "row_standard",
            "columns": {"rev": "1", "update": "INITIAL RELEASE", "status": "OBSOLETE"},
        },
        {
            "row_format": "row_standard",
            "columns": {"rev": "2", "update": "ADDED CABLES", "status": "OBSOLETE"},
        },
        {
            "row_format": "row_with_bubble",
            "columns": {
                "rev": {"instance_name": "REV-BUBBLE", "mpn": "REV-BUBBLE-ICON"},
                "update": ["USING BASIC SEGMENT", "GENERATOR MACRO"],
                "status": "OBSOLETE",
            },
        },
    ],
)
```

---

End of Requirements — rev2
