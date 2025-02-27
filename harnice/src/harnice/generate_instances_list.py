import yaml
import csv
import os
from utility import *
from os.path import basename, join
from inspect import currentframe

def generate_instances_list():
    # Create output directory if it doesn't exist
    os.makedirs(dirpath("boms"), exist_ok=True)

    with open(filepath("harness bom"), 'r') as bom_file:
        # Read the header line first
        header_line = bom_file.readline()
        header = header_line.strip().split("\t")
        
        # Identify indices from the header
        id_index = header.index("Id")
        mpn_index = header.index("MPN")
        desc_simple_index = header.index("Description Simple")
        supplier_index = header.index("Supplier")

        # Read the remaining data (if needed)
        bom_data = bom_file.read()
        bom_lines = bom_data.splitlines()

    # Load YAML file
    with open(filepath("wireviz yaml"), 'r') as yaml_file:
        yaml_data = yaml.safe_load(yaml_file)

    #try:
    with open(filepath("instances list"), mode='w', newline='', encoding="utf-8") as tsv_file:
        columns = ["instance name", "bom line", "backshell"]
        writer = csv.DictWriter(tsv_file, fieldnames=columns, delimiter='\t')
        writer.writeheader()

        #for each line in harness bom:
        for line in bom_lines:

            columns = line.strip().split("\t")
            current_desc_simple = columns[desc_simple_index]

            #if "Description Simple" == "Backshell" in harness bom (do this first because it informs rotation of others)
            if current_desc_simple == "Backshell":
                current_mpn = columns[mpn_index]
                
                #for each connector in yaml
                for connector_name, connector in yaml_data.get("connectors", {}).items():
                    # Check if any additional component is a Backshell with mpn equal to current_mpn
                    if any(
                        component.get("type") == "Backshell" and component.get("mpn") == current_mpn
                        for component in connector.get("additional_components", [])
                    ):
                        #TODO: add a line in connector list representing that backshell
                        new_row = {
                            "instance name": f"{connector_name}.bs",
                            "bom line": columns[id_index],
                            "backshell": ""
                        }
                        writer.writerow(new_row)

            if current_desc_simple == "Connector":
                current_mpn = columns[mpn_index]  

                #for each connector in yaml
                for connector_name, connector in yaml_data.get("connectors", {}).items():
                    #if "mpn" in yaml == "MPN" in harness bom
                    if connector.get("mpn") == current_mpn:

                        backshell = ""
                        #if connector has any backshell as an additional part
                        if any(
                            component.get("type") == "Backshell" for 
                            component in connector.get("additional_components", [])
                        ):
                            #TODO: this field should look up backshell part number
                            backshell = ""

                        #TODO: add a line in connector list
                        new_row = {
                            "instance name": connector_name,
                            "bom line": columns[id_index],
                            "backshell": backshell
                        }
                        writer.writerow(new_row)

if __name__ == "__main__":
    generate_instances_list()
