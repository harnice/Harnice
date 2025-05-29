import argparse
from harnice.commands import render, new

def main():
    parser = argparse.ArgumentParser(prog="harnice", description="Wire harness automation CLI")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-r", "--render", help="Render harness or system")
    group.add_argument("-n", "--new", help="Create a new component (part, tblock, flagnote)")
    args = parser.parse_args()

    if args.render:
        item_type = args.new
        if item_type == "harness":
            render.harness()
        elif item_type == "system":
            render.system()
        elif item_type == "part":
            render.undefined()
        elif item_type == "tblock":
            render.tblock()
        elif item_type == "titleblock":
            render.tblock()
        elif item_type == "flagnote":
            render.undefined()

    if args.new:
        item_type = args.new
        if item_type == "harness":
            new.create_harness()
        if item_type == "system":
            new.create_system()
        elif item_type == "part":
            new.create_part("")
        elif item_type == "tblock":
            new.create_titleblock()
        elif item_type == "titleblock":
            new.create_titleblock()
        elif item_type == "flagnote":
            new.create_flagnote()
        else:
            print(f"Unknown type for --new: {item_type}")

def prompt(text, default=None):
    p = f"{text}"
    if default:
        p += f" [{default}]"
    p += ": "
    return input(p).strip() or default