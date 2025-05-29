from dotenv import load_dotenv, dotenv_values
import os
from harnice import cli
from harnice.commands import render

def create_part(mfgmpn):
    library = cli.prompt("Which library do you want this in?", "public")
    
    while True:
        mfgmpn = cli.prompt("Enter a manufacturer and manufacturer part number", mfgmpn).strip()
        if mfgmpn:
            break
        print("MFG MPN cannot be blank. Please enter a value.")

    newstuff("part", library, mfgmpn)


def create_titleblock():
    library = cli.prompt("Which library do you want this in?", "public")
    
    while True:
        name = cli.prompt("What would you like to call it?")
        if name:
            break
        print("Name can't be blank. Please enter a value.")

    newstuff("tblock", library, name)

def create_flagnote():
    library = cli.prompt("Which library do you want this in?", "public")
    
    while True:
        name = cli.prompt("What would you like to call it?")
        if name:
            break
        print("Name can't be blank. Please enter a value.")

    newstuff("flagnote", library, name)

def newstuff(product_type, library, name):
    load_dotenv()

    library_path = os.getenv(library)
    if not library_path:
        raise ValueError(
            f"Environment variable '{library}' is not set. Add the path to this library from your harnice root directory."
        )

    if product_type == "part":
        library_subdir = "parts"
    elif product_type == "tblock":
        library_subdir = "titleblocks"
    elif product_type == "flagnote":
        library_subdir = "flagnotes"

    new_item_path = os.path.join(library_path, library_subdir, name)

    if os.path.exists(new_item_path):
        if cli.prompt("File already exists. Do you want to remove it?", "no") == "no":
            print("Exiting harnice")
            exit()
        else:
            import shutil
            shutil.rmtree(new_item_path)
    
    os.makedirs(new_item_path)

    cwd = os.getcwd()
    os.chdir(new_item_path)

    if product_type == "part":
        render.part()
    elif product_type == "tblock":
        render.tblock()
    elif product_type == "flagnote":
        render.flagnote()

    os.chdir(cwd)

    print()
    print(f"### New {product_type} {name} generated within library {library}!")
    print()
