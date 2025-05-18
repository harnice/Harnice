from harnice import (
    newstuff,
    cli
)

def create_part(mfgmpn):
    library = cli.prompt("Library", "public")
    newstuff.part(
        library,
        mfgmpn
    )

def create_titleblock(name):
    library = cli.prompt("Library", "public")
    size = cli.prompt("Size (e.g. 11x17, A4)", "11x17")
    newstuff.tblock(
        library,
        name,
        size
    )

def create_flagnote(description):
    library = cli.prompt("Library", "public")
    print(f"Would create flagnote '{description}' in library '{library}'")
    # TODO: generate flagnote data
