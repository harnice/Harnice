from pathlib import Path

# ========================================================
# DATA STRUCTURES
# ========================================================

md = [
    """# Feature Tree

When a python file (feature_tree.py) is called, a System Instances List is queried, and every instance that’s related to the associated KiCad net is brought in. 

Similar to systems, each harness has its own feature tree, and it acts as the primary collector for your design rules.

It is also in charge of producing outputs, like build drawings, formboard drawings, or wirelists. More on those later.


# File Formats

Harnice uses common file formats to store all of its data to improve portability and ease of interaction. Common formats in Harnice...
 - .csv (comma-separated value)
 - .tsv (tab-separated value; like csv but you can have commas in your data)
 - .py (plaintext file that contains Python syntax)

There are some standard file structures, called out by special names, that are used across many products. Regardless of the product type, the file should more or less do the same thing.

# Part Numbering

# File Structure

fileio.py contains functions that keep your files organized and easy to reference when they’re needed.

Products and macros are all supposed to have a function file_structure() that represents the file structure of the contents of that product on top of the current directory (rev folder).

Each value that contains a dict represents a directory, and each value that contains a string represents a file.

Keys are used for files to be more human readable.

You can add args as needed to describe more complicated structures.

When a product is rendered, that product’s file structure is automatically loaded into fileio.

You can reference files in that product by calling fileio.path(“file key”) from your script.
You can reference directories in that product by calling fileio.dirpath(“dirname”) from your script.

If you want to reference files that might not be defined in your product’s file structure (you’re running a bespoke macro with some weird content), you can temporarily pass a filepath dictionary into the function: fileio.path(“file key”, structure_dict={})

The same fileio functions can be called to regard different results depending on what structure_dict your current product, project, macro, etc has defined.

To “render” a product (harness, part, etc) with Harnice, the CLI will force you to operate in a “rev folder”
Revision data always stored in revision_history.tsv
Harnice will not render a revision if there’s data in the “status” field, i.e. “released” or “outdated”
Revision information can be referenced elsewhere, ex in pdf_generator
"""
]

harnice_dir = Path(__file__).resolve().parents[2]
path = harnice_dir / "docs" / "getting_started" / "_data_structures.md"
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text("".join(md), encoding="utf-8")

# ========================================================
# GIT INTEGRATION
# ========================================================

md = ["# Integrating Harnice with Git"]

harnice_dir = Path(__file__).resolve().parents[2]
path = harnice_dir / "docs" / "getting_started" / "_git_integration.md"
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text("".join(md), encoding="utf-8")


# ========================================================
# LIBRARIES
# ========================================================

md = [
    """Parts, macros, titleblocks, flagnotes, etc, should be re-used and referenced for any future use
Users are heavily encouraged to contribute to the public git repo for your cots parts
harnice-library-public
However, you can define paths to as many library repos as you want.
my-company-harnice-library
my-super-top-secret-harnice-library
You don’t even have to use git to control it if you don’t want!


# Library Flexibility
All parts in a library are version controlled per previous slide…

When importing an item from library, you can request different versions or overwrite imported libraries flexibly…
"""
]

harnice_dir = Path(__file__).resolve().parents[2]
path = harnice_dir / "docs" / "getting_started" / "_libraries.md"
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text("".join(md), encoding="utf-8")
