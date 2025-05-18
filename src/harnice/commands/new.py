def prompt(text, default=None):
    p = f"{text}"
    if default:
        p += f" [{default}]"
    p += ": "
    return input(p).strip() or default

def create_part():
    print("🛠️  Creating a new part")
    library = prompt("📦 Library", "public")
    name = prompt("📁 Part name")
    part_type = prompt("🔧 Type (connector/wire/label)", "connector")
    print(f"✅ Would create part '{name}' in '{library}' as '{part_type}'")
    # TODO: hook into new_library_stuff.py logic

def create_titleblock():
    print("📐 Creating a new titleblock")
    library = prompt("📦 Library", "public")
    name = prompt("📁 Titleblock name")
    print(f"✅ Would create titleblock '{name}' in '{library}'")
    # TODO: implement actual logic

def create_flagnote():
    print("📝 Creating a new flagnote")
    library = prompt("📦 Library", "public")
    name = prompt("🆔 Flagnote name")
    location = prompt("📍 Location (angle,distance)", "0,0")
    design = prompt("🎨 Design (Circle/Rectangle)", "Circle")
    print(f"✅ Would create flagnote '{name}' at {location} in '{library}' with design '{design}'")
    # TODO: implement actual logic
