# Harnice Macros

Macros are less fundamental commands, are revision controlled like parts, and offer a way for the user to call several instances while modifying each one slightly within your project.


A macro is a chunk of Python that has access to your project files or any other Python-capable function

When you call featuretree_utils.run_macro(), it will import the macro from a library and run it in your script

Some macros are designed to be used to build systems, build harnesses, or export contents “artifacts” from a harness instances list


# Build Macros

Intended to add or modify lines on an instances list based on a standard set of rules or instructions
Can read information from the instances list
Can read information from other support files
Examples
featuretree.runmacro(“import_wireviz_yaml”, “public”)
Reads a wireviz YAML (another commonly used harness design format)
featuretree. runmacro(“add_yellow_htshrk_to_plugs”, “kenyonshutt”)
You can write any rule or set of rules you want in Python, save it to your library, and call it from a harness feature tree.
This one, for example, might scour the instances list:
for plug in instances_list:
if item_type==plug:
instances_list.add(heatshrink, to cable near plug)


# Output Macros
Output Macros will scour the Instances List or other artifact outputs and make other things out of it
BOM
Formboard arrangement
PDF drawing sheet
Analysis calcs
Write your own!
