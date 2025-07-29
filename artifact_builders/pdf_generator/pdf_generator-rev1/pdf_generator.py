#=============== RUN WIREVIZ #===============
svg_utils.produce_multipage_harnice_output_pdf(page_setup_contents)
    # makes a PDF out of each svg in page setup


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
