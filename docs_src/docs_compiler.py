import runpy

def print_function_docs(fn,module_prefix=""):
    title = fn.__name__
    doc = fn.__doc__ or "No documentation provided."

    return (
        f'??? info "`{module_prefix}.{title}()`"\n\n'
        + "\n".join(f"    {line}" for line in doc.strip().splitlines())
        + "\n\n"
    )

if __name__ == "__main__":
    runpy.run_path("commands.py", run_name="__main__")
    runpy.run_path("fragments.py", run_name="__main__")
    runpy.run_path("getting_started.py", run_name="__main__")
    runpy.run_path("interacting_with_data.py", run_name="__main__")
    runpy.run_path("products.py", run_name="__main__")