from harnice import (
    newstuff,
    cli
)

def create_part(mfgmpn):
    library = cli.prompt("Which library do you want this in?", "public")
    
    while True:
        mfgmpn = cli.prompt("Enter a manufacturer and manufacturer part number", mfgmpn).strip()
        if mfgmpn:
            break
        print("MFG MPN cannot be blank. Please enter a value.")

    newstuff.part(library, mfgmpn)


def create_titleblock():
    library = cli.prompt("Which library do you want this in?", "public")
    name = cli.prompt("What would you like to call it?")
    size = cli.prompt("Size (e.g. 11x17, A4)", "11x17")
    newstuff.tblock(
        library,
        name,
        size
    )

def create_flagnote():
    library = cli.prompt("Library", "public")
    print(f"Would create flagnote '{description}' in library '{library}'")
    # TODO: generate flagnote data
