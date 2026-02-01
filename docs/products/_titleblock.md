# Titleblocks
A page SVG, usually with your name or company logo, that makes your drawings look professional.

## File Structure

Reference the files in your product by calling `fileio.path("file key")` from your script. They'll automatically use this structure:

```
fileio.dirpath("part_directory")       |-- yourpn/
                                           |-- yourpn-earlier-revs/
                                           |-- revhistory.csv
fileio.dirpath("rev_directory")            L-- yourpn-revX/
fileio.path("params")                          |-- yourpn-revX-params.json
fileio.path("drawing")                         |-- yourpn-revX-drawing.svg
fileio.path("attributes")                      L-- yourpn-revX-attributes.json
```
