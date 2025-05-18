import argparse
from harnice.commands import render, new

def main():
    parser = argparse.ArgumentParser(prog="harnice", description="Wire harness automation CLI")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--render", choices=["harness", "system"], help="Render harness or system")
    group.add_argument("--new", choices=["part", "tblock", "flagnote"], help="Create a new editable component")
    args = parser.parse_args()

    if args.render == "harness":
        render.run_harness()
    elif args.render == "system":
        render.run_system()
    elif args.new == "part":
        new.create_part()
    elif args.new == "tblock":
        new.create_titleblock()
    elif args.new == "flagnote":
        new.create_flagnote()
