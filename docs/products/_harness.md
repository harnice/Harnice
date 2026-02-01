# Harnesses
A physical assembly that contains a set of electrical circuits that satisfies a channel map. Can also contain other parts and instructions about how to be built. 


---

## How to define a new harness

1. Make a folder for the part number of your harness somewhere on your computer. Run Harnice Render, which will generate an example harness that you can then edit.

    ??? info "Rendering a Product"

        {% include-markdown "fragments/how-to-render.md" %}

    You can also lightweight render if you want to bypass some of the checks.

    ??? info "Lightweight Rendering a Product"

        {% include-markdown "fragments/lightweight_rendering.md" %}

1. Edit the attributes of your new harness.

    ??? info "Editing the Attributes of a Product"

        {% include-markdown "fragments/editing_attributes.md" %}

1. Edit the formboard graph of your new harness.

    ??? info "Editing the Formboard Graph of a Product"

        {% include-markdown "fragments/editing_formboard_graph.md" %}


## File Structure

Reference the files in your product by calling `fileio.path("file key")` from your script. They'll automatically use this structure:

```
fileio.dirpath("part_directory")                    |-- yourpn/
                                                        |-- earlier revs/
                                                        |-- revhistory.csv
fileio.dirpath("rev_directory")                                                                      L-- your rev/
fileio.path("feature tree")                                 |-- yourpn-revX-feature_tree.py
fileio.path("instances list")                               |-- yourpn-revX-instances_list.tsv
fileio.path("formboard graph definition png")               |-- yourpn-revX-formboard_graph_definition.png
fileio.path("library history")                              |-- yourpn-revX-library_import_history.tsv
                                                            L-- interactive_files/
fileio.path("formboard graph definition")                       L-- yourpn-revX.formboard_graph_definition.tsv
```
