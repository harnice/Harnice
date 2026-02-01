# Flagnotes
A bubble shape on a drawing that usually points to something via a leader arrow.

## File Structure

Reference the files in your product by calling `fileio.path("file key")` from your script. They'll automatically use this structure:

```
fileio.dirpath("part_directory")       |-- yourpn/
                                           |-- yourpn-earlier-revs/
                                           |-- revhistory.csv
fileio.dirpath("rev_directory")            L-- yourpn-revX/
fileio.path("params")                          |-- yourpn-revX-params.json
fileio.path("drawing")                         L-- yourpn-revX-drawing.svg
```
