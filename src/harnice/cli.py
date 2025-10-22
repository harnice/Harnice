import argparse
import os
import sys
from harnice import fileio
from harnice.products import (
    device,
    harness,
    part,
    flagnote,
    tblock,
    system,
    disconnect,
    cable,
)


def ensure_cwd_exists():
    try:
        cwd = os.getcwd()
    except (FileNotFoundError, PermissionError):
        sys.exit(
            "Error: The current working directory is invalid "
            "(it may have been deleted or you lack permission to access it)."
        )

    if not os.path.exists(cwd):
        sys.exit(f"Error: The current working directory no longer exists: {cwd}")


def main():
    ensure_cwd_exists()

    parser = argparse.ArgumentParser(
        prog="harnice", description="Wire harness automation CLI"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "-r",
        "--render",
        choices=[
            "harness",
            "system",
            "part",
            "flagnote",
            "device",
            "disconnect",
            "tblock",
            "titleblock",
            "cable",
        ],
        help="Render a product type",
    )
    group.add_argument(
        "-l",
        "--lightweight",
        choices=["device"],
        help="Render a product type quickly without performing all checks",
    )
    group.add_argument(
        "--newrev",
        action="store_true",
        help="Create a new revision in the current working directory",
    )

    args = parser.parse_args()

    # Handle new revision creation
    if args.newrev:
        fileio.newrev()
        return

    # Figure out which product type string to use
    product_type = args.render or args.lightweight
    fileio.set_product_type(product_type.lower())

    if args.render:
        render_map = {
            "harness": harness.render,
            "system": system.render,
            "part": part.render,
            "flagnote": flagnote.render,
            "device": device.render,
            "disconnect": disconnect.render,
            "cable": cable.render,
            "tblock": tblock.render,
            "titleblock": tblock.render,  # alias
        }
        render_map[args.render.lower()]()

    elif args.lightweight:
        device.lightweight_render()


def prompt(text, default=None):
    p = f"{text}"
    if default:
        p += f" [{default}]"
    p += ": "
    return input(p).strip() or default
