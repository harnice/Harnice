#=============== PATHS ===============
def path(target_value):
    artifact_path = os.path.join(fileio.dirpath("artifacts"), "wireviz_builder")
    os.makedirs(artifact_path, exist_ok=True)
    artifact_id_path = os.path.join(artifact_path, artifact_id)
    os.makedirs(artifact_id_path, exist_ok=True)
    if target_value == "wireviz bom":
        return os.path.join(artifact_id_path, f"{fileio.partnumber("pn-rev")}-wireviz_bom.tsv")
    if target_value == "wireviz html":
        return os.path.join(artifact_id_path, f"{fileio.partnumber("pn-rev")}-wireviz_html.html")
    if target_value == "wireviz png":
        return os.path.join(artifact_id_path, f"{fileio.partnumber("pn-rev")}-wireviz_png.png")
    if target_value == "wireviz svg":
        return os.path.join(artifact_id_path, f"{fileio.partnumber("pn-rev")}-wireviz-svg.svg")
    else:
        raise KeyError(f"Filename {target_value} not found in wireviz_builder file tree")

#=============== RUN WIREVIZ #===============
run_wireviz.generate_esch()