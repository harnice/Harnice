#=============== PATHS ===============
def path(target_value):
    #artifact_path gets passed in as a global from the caller
    if target_value == "wireviz bom":
        return os.path.join(artifact_path, f"{fileio.partnumber("pn-rev")}-wireviz_bom.tsv")
    if target_value == "wireviz html":
        return os.path.join(artifact_path, f"{fileio.partnumber("pn-rev")}-wireviz_html.html")
    if target_value == "wireviz png":
        return os.path.join(artifact_path, f"{fileio.partnumber("pn-rev")}-wireviz_png.png")
    if target_value == "wireviz svg":
        return os.path.join(artifact_path, f"{fileio.partnumber("pn-rev")}-wireviz-svg.svg")
    else:
        raise KeyError(f"Filename {target_value} not found in wireviz_builder file tree")

#=============== RUN WIREVIZ #===============
run_wireviz.generate_esch()