import argparse
from harnice.commands import render, new

def main():
    parser = argparse.ArgumentParser(prog="harnice", description="Wire harness automation CLI")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-r", "--render", choices=["harness", "system"], help="Render harness or system")
    group.add_argument("-n", "--new", nargs=2, metavar=("TYPE", "VALUE"), help="Create a new component (part, tblock, flagnote)")
    args = parser.parse_args()

    if args.render == "harness":
        render.render_harness()
    elif args.render == "system":
        render.run_system()

    if args.new:
        item_type, value = args.new
        if item_type == "part":
            new.create_part(mfgmpn=value)
        elif item_type == "tblock":
            new.create_titleblock(name=value)
        elif item_type == "flagnote":
            new.create_flagnote(description=value)
        else:
            print(f"Unknown type for --new: {item_type}")

def prompt(text, default=None):
    p = f"{text}"
    if default:
        p += f" [{default}]"
    p += ": "
    return input(p).strip() or default