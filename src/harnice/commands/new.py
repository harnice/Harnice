from harnice import (
    newstuff
)

def prompt(text, default=None):
    p = f"{text}"
    if default:
        p += f" [{default}]"
    p += ": "
    return input(p).strip() or default

def create_part(mfgmpn):
    library = prompt("Library", "public")
    mfgmpn = prompt("ID (mfg mpn)")
    newstuff.part(
        library,
        mfgmpn
    )

def create_titleblock(name):
    library = prompt("Library", "public")
    size = prompt("Size (e.g. 11x17, A4)", "11x17")
    newstuff.tblock(
        library,
        name,
        size
    )

def create_flagnote(description):
    library = prompt("Library", "public")
    print(f"Would create flagnote '{description}' in library '{library}'")
    # TODO: generate flagnote data
