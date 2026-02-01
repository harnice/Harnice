# Parts
Buyable or buildable child item that goes into a harness.


## File Structure

Reference the files in your product by calling `fileio.path("file key")` from your script. They'll automatically use this structure:

```
fileio.dirpath("part_directory")       |-- yourpn/
                                           |-- yourpn-earlier-revs/
                                           |-- revhistory.csv
fileio.dirpath("rev_directory")            L-- yourpn-revX/
fileio.path("drawing")                         |-- yourpn-revX-drawing.svg
fileio.path("drawing png")                     |-- yourpn-revX-drawing.png
fileio.path("attributes")                      L-- yourpn-revX-attributes.json
```
