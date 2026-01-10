import runpy
import inspect
import re
from types import ModuleType

def print_function_docs(fn,module_prefix=""):
    title = fn.__name__
    doc = fn.__doc__ or "No documentation provided."

    return (
        f'??? info "`{module_prefix}.{title}()`"\n\n'
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

        # Optionally strip a leading '#' if you accidentally wrote "#The ..."
        if desc.startswith("#"):
            desc = desc[1:].lstrip()

        md.append(f'=== "`{name}`"\n\n')
        md.append(f"    {desc}\n\n")

    return "".join(md)

if __name__ == "__main__":
    runpy.run_path("commands.py", run_name="__main__")
    runpy.run_path("fragments.py", run_name="__main__")
    runpy.run_path("getting_started.py", run_name="__main__")
    runpy.run_path("interacting_with_data.py", run_name="__main__")
    runpy.run_path("products.py", run_name="__main__")