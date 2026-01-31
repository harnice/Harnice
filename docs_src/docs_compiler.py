import runpy
import inspect
import re
from types import ModuleType
from pathlib import Path

# NOTE THAT ANY MD FILE OR DIRECTORY STARTING IN _ IS DEFINED BY CODE RAN BY THIS FULE
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

        # 🔹 Expand escaped newlines
        desc = desc.replace("\\n", "\n")

        # 🔹 Re-indent multiline text for MkDocs
        formatted_desc = "\n".join("    " + l for l in desc.splitlines())

        md.append(f'=== "`{name}`"\n\n')
        md.append(f"{formatted_desc}\n\n")

    return "".join(md)


if __name__ == "__main__":
    runpy.run_path("commands.py", run_name="__main__")
    runpy.run_path("getting_started.py", run_name="__main__")
    runpy.run_path("interacting_with_data.py", run_name="__main__")
    runpy.run_path("products.py", run_name="__main__")
