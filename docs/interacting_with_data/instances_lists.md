## What it is
`*-instances_list.tsv` is a tab-separated value list of every physical or notional thing, drawing element, or concept that is the single source of truth for the product you are working on.

A list of every single item, idea, note, part, instruction, circuit, literally anything that comprehensively describes how to build that harness or system
TSV (tab-separated-values, big spreadsheet)
Declined alternatives: STEP files, schematics, dictionaries not general, descriptive, or human readable enough


## How to Import
Including the instances list module into your py file will allow you to access the functions of this module. Copy and paste it into the top of your py file.
`from harnice.lists import instances_list`
##Commands:
??? info "`instances_list.new_instance()`"

    New Instance
    
    instances_list.new_instance(
        instance_name,
        instance_data,
        ignore_duplicates=False
    )
    
    Add a new instance to your instances list.
    
        instance_name is a string and must be unique within the list.
        instance_data is a dictionary of columns (above). You may or may not include instance_name in this dict, though if you do and it doesn't match the argument, the code will fail.
        Setting ignore_duplicates to True will cause the line to pass silently if you try to add an instance with an instance_name that already exists. By default, False, if you do this, the code will raise an error if you try to add a duplicate instance_name.
    
        Args:
            instance_name: string, must be unique within the list
            instance_data: dictionary of columns (above)
            ignore_duplicates: boolean, default False
    
        Returns:
            -1 if the instance was added successfully, otherwise raises an error

??? info "`instances_list.modify()`"

    No documentation provided.

??? info "`instances_list.remove_instance()`"

    No documentation provided.

??? info "`instances_list.new()`"

    No documentation provided.

??? info "`instances_list.assign_bom_line_numbers()`"

    No documentation provided.

??? info "`instances_list.attribute_of()`"

    No documentation provided.

??? info "`instances_list.instance_in_connector_group_with_item_type()`"

    No documentation provided.

??? info "`instances_list.list_of_uniques()`"

    No documentation provided.

