1. Navigate to your device folder (`cd` in command line). You don't need to make a rev folder yet, just make sure your command line is in a folder you want to represent the device you're working on. 

1. Harnice render it (`harnice -r`). It should walk you through the following steps then render an example:

    1. `No valid Harnice file structure detected in 'your_part_number'. Create new PN here? [y]: ` hit enter

    1. `Enter revision number [1]:` hit enter for rev1 or type "A" or whatever you want your first rev to be called
    
    1. `What product type are you working on? (harness, system, device, etc.): ` type "device"
    
    1. `Enter a description of this device [DEVICE, FUNCTION, ATTRIBUTES, etc.]:` self-explanatory
    
    1. `Enter a description for this revision [INITIAL RELEASE]: ` hit enter, otherwise type the goal of the first revision