import argparse
import os
from harnice import fileio
from harnice.products import device, harness, part, flagnote, tblock, system


def main():
    try:
        _ = os.getcwd()
    except FileNotFoundError:
        raise RuntimeError(
            "Your command line is in a directory that doesn't exist. "
            "(maybe you were working on a file you just tried to delete?)"
        )

    parser = argparse.ArgumentParser(
        prog="harnice",
        description="Wire harness automation CLI"
    )
    parser.add_argument(
        "-r", "--render",
        required=True,
        choices=["harness", "system", "part", "flagnote", "device", "tblock", "titleblock"],
        help="Render a product type"
    )
    args = parser.parse_args()

    render_type = args.render.lower()
    fileio.set_product_type(render_type)

    render_map = {
        "harness": harness.render,
        "system": system.render,
        "part": part.render,
        "flagnote": flagnote.render,
        "device": device.render,
        "tblock": tblock.render,
        "titleblock": tblock.render,  # alias
    }

    if render_type in render_map:
        render_map[render_type]()
    else:
        print(f"Unknown type for --render: {render_type}")


def prompt(text, default=None):
    p = f"{text}"
    if default:
        p += f" [{default}]"
    p += ": "
    return input(p).strip() or default


if __name__ == "__main__":
    main()
