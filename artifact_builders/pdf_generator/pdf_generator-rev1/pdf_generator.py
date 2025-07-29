
#=============== PATHS ===============
def path(target_value):
    artifact_path = os.path.join(fileio.dirpath("artifacts"), "pdf_generator")
    os.makedirs(artifact_path, exist_ok=True)
    artifact_id_path = os.path.join(artifact_path, artifact_id)
    os.makedirs(artifact_id_path, exist_ok=True)
    if target_value == "page setup":
        return os.path.join(artifact_id_path, f"{fileio.partnumber("pn-rev")}-page_setup.json")
    if target_value == "output pdf":
        return os.path.join(artifact_id_path, f"{fileio.partnumber("pn-rev")}-output.pdf")
    if target_value == "page svgs":
        os.mkdirs(os.path.join(artifact_id_path, "page_svgs"), exist_ok=True)
        return os.path.join(artifact_id_path, "page svgs")
    else:
        raise KeyError(f"Filename {target_value} not found in pdf_generator file tree")

def update_page_setup_json():
    # === Titleblock Defaults ===
    blank_setup = {
        "pages": [
            {
                "name": "page1",
                "supplier": "public",
                "titleblock": "harnice_tblock-11x8.5",
                "text_replacements": {
                    "tblock-key-desc": "pull_from_revision_history(desc)",
                    "tblock-key-pn": "pull_from_revision_history(pn)",
                    "tblock-key-drawnby": "pull_from_revision_history(drawnby)",
                    "tblock-key-rev": "pull_from_revision_history(rev)",
                    "tblock-key-releaseticket": "",
                    "tblock-key-scale": "A",
                    "tblock-key-sheet": "autosheet"
                },
                "show_items": [
                    "bom",
                    "buildnotes",
                    "revhistory"
                ]
            }
        ],
        "formboards": {
            "formboard1": {
                "scale": "A",
                "rotation": 0,
                "hide_instances": {}
            }
        },
        "show_items_example_options":[
            "bom",
            "buildnotes",
            "revhistory"
        ]
    }

    # === Load or Initialize Titleblock Setup ===

    page_setup_path = fileio.dirpath("artifacts")
    if not os.path.exists(path("output svg")) or os.path.getsize(path("output svg")) == 0:
        with open(path("output svg"), "w", encoding="utf-8") as f:
            json.dump(blank_setup, f, indent=4)
        tblock_data = blank_setup
    else:
        try:
            with open(path("output svg"), "r", encoding="utf-8") as f:
                tblock_data = json.load(f)
        except json.JSONDecodeError:
            with open(path("output svg"), "w", encoding="utf-8") as f:
                json.dump(blank_setup, f, indent=4)
            tblock_data = blank_setup

    with open(path("output svg"), "w", encoding="utf-8") as f:
        json.dump(tblock_data, f, indent=4)

    return tblock_data


def produce_multipage_harnice_output_pdf(page_setup_contents):
    partnumber = fileio.partnumber("pn-rev")
    svg_dir = fileio.dirpath("page_setup")
    output_pdf = fileio.path("harnice output")

    temp_pdfs = []
    inkscape_bin = "/Applications/Inkscape.app/Contents/MacOS/inkscape"  # adjust if needed

    for page in page_setup_contents.get("pages", []):
        page_name = page.get("name")
        svg_filename = f"{partnumber}.{page_name}.svg"
        svg_path = os.path.join(svg_dir, svg_filename)

        if not os.path.exists(svg_path):
            raise FileNotFoundError(f"[ERROR] SVG not found: {svg_path}")

        pdf_path = svg_path.replace(".svg", ".temp.pdf")

        subprocess.run([
            inkscape_bin, svg_path,
            "--export-type=pdf",
            f"--export-filename={pdf_path}"
        ], check=True)

        temp_pdfs.append(pdf_path)

    # Merge all PDFs
    subprocess.run(["pdfunite"] + temp_pdfs + [output_pdf], check=True)

    # Optional cleanup
    for temp in temp_pdfs:
        os.remove(temp)
