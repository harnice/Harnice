import argparse
import os
from harnice import (
    fileio,
    system
)
from harnice.commands import render, box

def main():
    try:
        _ = os.getcwd()
    except FileNotFoundError:
        raise RuntimeError(
            "Your command line is in a directory that doesn't exist."
            "(maybe you were working on a file you just tried to delete?)"
        )

    parser = argparse.ArgumentParser(prog="harnice", description="Wire harness automation CLI")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-r", "--render", help="Render harness or system")
    group.add_argument("-n", "--new", help="Create a new component (part, tblock, flagnote)")
    args = parser.parse_args()

    if args.render:
        render_type = args.render.lower()
        fileio.set_product_type(render_type)

        if render_type == "harness":
            render.harness()
        elif render_type == "system":
            system.render()
        elif render_type == "part":
            render.part()
        elif render_type == "flagnote":
            render.flagnote()
        elif render_type == "box":
            box.render()
        elif render_type in {"tblock", "titleblock"}:
            render.tblock()
        else:
            print(f"Unknown type for --render: {render_type}")

def prompt(text, default=None):
    p = f"{text}"
    if default:
        p += f" [{default}]"
    p += ": "
    return input(p).strip() or default