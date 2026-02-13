"""Current render context: part number, revision, product, and file structure.

The CLI and `fileio` set these before running a product. Scripts can read `state.pn`,
`state.rev`, and `state.partnumber(format)`; `state.file_structure` is used by `fileio`
when resolving path keys.
"""

import re


# not initializing these variables so that a NameError is raised if they are not set
def set_pn(x):
    """Set the current part number (e.g. `"mypart"`). Called by `fileio.verify_revision_structure()`."""
    global pn
    pn = x


def set_rev(x):
    """Set the current revision number (integer). Called by `fileio.verify_revision_structure()`."""
    global rev
    rev = x


def set_product(x):
    """Set the current product type (e.g. `"harness"`, `"system"`)."""
    global product
    product = x


def set_net(x):
    """Set the current net context (used during render)."""
    global net
    net = x


def set_file_structure(x):
    """Set the default file structure dict used by `fileio.path()` and `fileio.dirpath()`.

The CLI calls this with the current product's `file_structure()` result.
    """
    global file_structure
    file_structure = x


def partnumber(format):
    """Return the current part number and/or revision in the requested format.

Assumes `state.pn` and `state.rev` are set (e.g. by `fileio.verify_revision_structure()`).
For a part `"mypart"` and rev `1`:

**Args:**

- **format** — One of:
    - `"pn-rev"`: full part-rev string, e.g. `"mypart-rev1"`
    - `"pn"`: part number only, e.g. `"mypart"`
    - `"rev"`: revision label, e.g. `"rev1"`
    - `"R"`: revision number only, e.g. `"1"`

**Returns:** The requested substring of `"pn-revRev"` (e.g. `"mypart-rev1"`) (`str`).

**Raises:** `ValueError` if **format** is not one of the options above.
    """
    pn_rev = f"{pn}-rev{rev}"

    if format == "pn-rev":
        return pn_rev

    elif format == "pn":
        match = re.search(r"-rev", pn_rev)
        if match:
            return pn_rev[: match.start()]

    elif format == "rev":
        match = re.search(r"-rev", pn_rev)
        if match:
            return pn_rev[match.start() + 1 :]

    elif format == "R":
        match = re.search(r"-rev", pn_rev)
        if match:
            return pn_rev[match.start() + 4 :]

    else:
        raise ValueError("Function 'partnumber' not presented with a valid format")
