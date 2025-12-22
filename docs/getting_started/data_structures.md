# Feature Tree

When a python file (feature_tree.py) is called, a System Instances List is queried, and every instance that’s related to the associated KiCad net is brought in. 

Similar to systems, each harness has its own feature tree, and it acts as the primary collector for your design rules.

It is also in charge of producing outputs, like build drawings, formboard drawings, or wirelists. More on those later.


# File Formats

Harnice uses common file formats to store all of its data to improve portability and ease of interaction. Common formats in Harnice...
 - .csv (comma-separated value)
 - .tsv (tab-separated value; like csv but you can have commas in your data)
 - .py (plaintext file that contains Python syntax)

There are some standard file structures, called out by special names, that are used across many products. Regardless of the product type, the file should more or less do the same thing.