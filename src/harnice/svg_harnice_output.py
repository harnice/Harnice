def update_harnice_output():
    if file does not exist fileio.path("harnice output"):

        #initialize the svg
        collected_attrs = {
            "xmlns": "http://www.w3.org/2000/svg",
            "version": "1.1",
            "font-family": "Arial",
            "font-size": "8",
            "width": "1056.0",
            "height": "816.0",
            "viewBox": "0 0 1056.0 816.0"
        }

    else:
        #save entire contents of the svg to a variable
    
    #chatgpt: make a group with id=support-do-not-edit-contents-start

    #track where the contents groups end up
    group_position = [0, -1600]
    position_x_delta = 1800

    #keep track of what to replace later
    groups_to_replace = ''

    #build the group structure of the svg only
    for each svg_master in fileio.dirpath("master_svgs"):
        #append group to support-do-not-edit with id={svg_master}-contents-start and translate=group_position
        #append group to support-do-not-edit with id={svg_master}-contnets-end
        #append svg_master to groups_to_replace

    #add all to svg and save file to 

    #conduct the actual replacement process
    for each svg_master in groups_to_replace:
        find_and_replace_svg_group(
            fileio.path("harnice output contents"), 
            os.path.join(fileio.dirpath("master_svgs"), svg_master), 
            svg_master, 
            svg_master
        )
        