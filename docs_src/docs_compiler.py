import runpy
import inspect
import re
from types import ModuleType
from pathlib import Path

# Import state module for setting mock values
try:
    from harnice import state
except ImportError:
    state = None

# NOTE THAT ANY MD FILE OR DIRECTORY STARTING IN _ IS DEFINED BY CODE RAN BY THIS FILE
# ALL ELSE IS MANUALLY DEFINED.


def harnice_dir():
    return Path(__file__).resolve().parents[1]


def commands_header(module_prefix):
    string = "\n---\n##Commands:\n"
    string += f"*Use the following functions by first importing the module in your script like this: \n```python\nfrom harnice.lists import {module_prefix}\n```\n then use as written.*\n"
    return string


def columns_header(module_prefix, additional_columns=False):
    string = "\n---\n##Columns \n"
    string += (
        f"*Columns are automatically generated when `{module_prefix}.new()` is called. "
    )
    if additional_columns:
        string += "Additional columns for this kind of list may be added by the user.*"
    else:
        string += "Additional columns are not supported and may result in an error when parsing.*"
    string += "\n"
    return string


def print_function_docs(fn, module_prefix=""):
    name = fn.__name__
    sig = inspect.signature(fn)
    doc = fn.__doc__ or "Documentation needed."

    full_name = f"{module_prefix}.{name}{sig}"

    return (
        f'??? info "`{full_name}`"\n\n'
        + "\n".join(f"    {line}" for line in doc.strip().splitlines())
        + "\n\n"
    )


def columns_to_markdown(module: ModuleType, var_name: str) -> str:
    """
    Read `var_name = [...]` from the module's source file and convert
    inline-commented entries like:
        "channel_id",  # Unique identifier
    into MkDocs tab markdown:
        === "`channel_id`"
            Unique identifier
    Supports escaped newlines \\n inside comments.
    """
    module_path = inspect.getsourcefile(module)
    if not module_path:
        raise RuntimeError(f"Can't locate source file for module {module.__name__!r}")

    text = open(module_path, "r", encoding="utf-8").read()

    # Grab the list block: VAR_NAME = [ ... ]
    block_re = re.compile(
        rf"^{re.escape(var_name)}\s*=\s*\[\s*(?P<body>.*?)^\]\s*$",
        re.MULTILINE | re.DOTALL,
    )
    m = block_re.search(text)
    if not m:
        raise ValueError(f"Couldn't find {var_name} = [...] in {module_path}")

    body = m.group("body")

    # Parse lines like: "name",  # description
    item_re = re.compile(r'"(?P<name>[^"]+)"\s*,?\s*#\s*(?P<desc>.*)\s*$')

    md = []
    for line in body.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        mm = item_re.search(line)
        if not mm:
            continue

        name = mm.group("name").strip()
        desc = mm.group("desc").rstrip()

        # Optionally strip accidental extra "#"
        if desc.startswith("#"):
            desc = desc[1:].lstrip()

        # Expand escaped newlines
        desc = desc.replace("\\n", "\n")

        # Re-indent multiline text for MkDocs
        formatted_desc = "\n".join("    " + line for line in desc.splitlines())

        md.append(f'=== "`{name}`"\n\n')
        md.append(f"{formatted_desc}\n\n")

    return "".join(md)



def file_structure_to_markdown(product_module: ModuleType) -> str:
    """
    Takes a product module (e.g., harness.py) and returns its file structure
    in markdown tree format using | and -- characters.

    The product module must have a file_structure() function that returns
    a dictionary where:
    - String values represent files
    - Dictionary values represent directories

    This function automatically sets mock state values (pn="yourpn", rev="X")
    before calling file_structure() to handle state-dependent file structures.

    Args:
        product_module: The module object (e.g., from importlib.import_module)

    Returns:
        Markdown string with tree structure using | and -- format

    Example:
        ```python
        import importlib
        from harnice.products import harness

        markdown_tree = file_structure_to_markdown(harness)
        ```
    """
    if not hasattr(product_module, "file_structure"):
        raise AttributeError(
            f"Module {product_module.__name__} does not have a file_structure() function"
        )

    # Set mock state values if state module is available
    old_pn = None
    old_rev = None
    if state is not None:
        # Save current state if it exists (check module globals)
        state_globals = state.__dict__
        if "pn" in state_globals:
            old_pn = state_globals.get("pn")
        if "rev" in state_globals:
            old_rev = state_globals.get("rev")

        # Set mock values
        state.set_pn("yourpn")
        state.set_rev("X")

    try:
        structure_dict = product_module.file_structure()
    finally:
        # Restore original state if it existed
        if state is not None:
            if old_pn is not None:
                state.set_pn(old_pn)
            if old_rev is not None:
                state.set_rev(old_rev)

    if not isinstance(structure_dict, dict):
        raise ValueError(
            f"file_structure() must return a dictionary, got {type(structure_dict)}"
        )

    def _find_max_path_length(d, current_max=0):
        """Recursively find the maximum fileio.path() call length."""
        for key, value in d.items():
            if isinstance(value, dict):
                current_max = _find_max_path_length(value, current_max)
            else:
                path_call = f'fileio.path("{value}")'
                current_max = max(current_max, len(path_call))
        return current_max

    # Find max path length across entire structure
    max_path_length = _find_max_path_length(structure_dict)
    # Also consider the dirpath calls
    max_path_length = max(max_path_length, len('fileio.dirpath("part_directory")'))
    max_path_length = max(max_path_length, len('fileio.dirpath("rev_directory")'))

    def _dict_to_tree(d, prefix="", is_last=True):
        """
        Recursively convert dictionary to tree format.

        Args:
            d: Dictionary to convert
            prefix: Current prefix for indentation (| or spaces)
            is_last: Whether this is the last item at this level
        """
        lines = []
        items = list(d.items())

        for i, (key, value) in enumerate(items):
            is_last_item = i == len(items) - 1

            # Determine the connector for this item
            if is_last_item:
                connector = "L-- "
                next_prefix = prefix + "    "
            else:
                connector = "|-- "
                next_prefix = prefix + "|   "

            # Determine if value is a directory (dict) or file (string)
            if isinstance(value, dict):
                # It's a directory - show directory name with connector
                name = f"{key}/"
                lines.append({"type": "dir", "prefix": prefix, "connector": connector, "name": name})
                # Recursively process the directory contents
                lines.extend(_dict_to_tree(value, next_prefix, is_last_item))
            else:
                # It's a file - store path_call and filename separately for formatting
                path_call = f'fileio.path("{value}")'
                filename = key
                lines.append({
                    "type": "file",
                    "prefix": prefix,
                    "connector": connector,
                    "path_call": path_call,
                    "filename": filename
                })

        return lines

    tree_items = _dict_to_tree(structure_dict)

    # Build the full tree with part_directory and rev_directory levels
    full_tree_lines = []

    # Part directory level
    part_dir_padding = " " * 7  # Space before |-- yourpn/
    part_dir_line = 'fileio.dirpath("part_directory")'.ljust(max_path_length) + part_dir_padding + "|-- yourpn/"
    full_tree_lines.append(part_dir_line)
    
    # Earlier revs and revhistory.csv at part number level
    pn_level_indent = max_path_length + len(part_dir_padding) + 4  # +4 for "|-- "
    full_tree_lines.append(" " * pn_level_indent + "|-- earlier revs/")
    full_tree_lines.append(" " * pn_level_indent + "|-- revhistory.csv")

    # Rev directory level - indented under yourpn/
    rev_dir_line = 'fileio.dirpath("rev_directory")'.ljust(max_path_length) + " " * pn_level_indent + "L-- your rev/"
    full_tree_lines.append(rev_dir_line)

    # Calculate the column where file connectors should align (under "your rev/")
    connector_col = pn_level_indent + 4  # +4 for "L-- "

    # Find the last root-level item (items with empty prefix)
    last_root_idx = -1
    for i, item in enumerate(tree_items):
        if item["prefix"] == "":
            last_root_idx = i

    # Process all tree items
    for i, item in enumerate(tree_items):
        is_root_level = item["prefix"] == ""

        if item["type"] == "file":
            # Format: path_call (aligned) + spacing + prefix + connector + filename
            path_call = item["path_call"]
            prefix = item["prefix"]
            connector = item["connector"]
            filename = item["filename"]
            
            # Align path_call, then add spacing to reach connector column, then add prefix structure
            aligned_path = path_call.ljust(max_path_length)
            spacing = " " * (connector_col - max_path_length)
            
            line = aligned_path + spacing + prefix + connector + filename
            full_tree_lines.append(line)
                
        else:  # directory
            prefix = item["prefix"]
            connector = item["connector"]
            name = item["name"]
            
            # All items (root and nested) should maintain their prefix structure
            line = " " * connector_col + prefix + connector + name
            
            full_tree_lines.append(line)

    tree_text = "\n".join(full_tree_lines)

    # Add header and wrap in code blocks
    return f'\n\n## File Structure\n\nReference the files in your product by calling `fileio.path("file key")` from your script. They\'ll automatically use this structure:\n\n```\n{tree_text}\n```\n'


if __name__ == "__main__":
    runpy.run_path("commands.py", run_name="__main__")
    runpy.run_path("getting_started.py", run_name="__main__")
    runpy.run_path("interacting_with_data.py", run_name="__main__")
    runpy.run_path("products.py", run_name="__main__")
    runpy.run_path("fragments.py", run_name="__main__")
