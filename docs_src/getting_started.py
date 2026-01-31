from pathlib import Path

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
