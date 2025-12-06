📝 Harnice Table Requirements (rev2)

## 1. Table Layout Rules

The table anchor applies to the header row.

Valid header anchor points:
- top-left
- top-right
- bottom-left
- bottom-right

The direction property determines where content rows are placed relative to the header:
- down → rows appear below the header
- up → rows appear above the header

---

## 2. Format Structure

The format dictionary defines appearance, structure, layout, and style behavior. Any key not listed as a reserved property is treated as a named row format.

```python
format = {
    "globals": {...},
    "header_format": {...},
    "columns": {...},
    "origin_corner": "...",
    "direction": "up | down",
    "row_standard": {...},
    "row_with_bubble": {...},
}
```

**Required Fields:**
- globals
- header_format
- columns
- origin_corner
- direction
- one or more `row_*` format definitions

**Row format must include:**
- row_height

**Optional formatting:**
- fill color
- font size / weight
- justification
- border width/style
- text alignment behavior

**Style resolution order:**

`row_format → column → globals`

---

## 3. Column Configuration

**Required:**
- name
- **fixed width**

**Optional:**
- justify
- valign

**Example:**

```json
"columns": {
  "rev": { "name": "rev", "width": 60, "justify": "center" },
  "update": { "name": "update", "width": 260, "justify": "left" },
  "status": { "name": "status", "width": 120, "justify": "center" }
}
```

Column order in this block defines render order.

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
