import yaml
import csv
import os
from utility import pn_from_dir
from os.path import basename, join
from inspect import currentframe

def generate_connector_list():

    # Define the YAML filename
    filename = f"{pn_from_dir()}.yaml"

    # Load YAML file
    try:
        with open(filename, 'r') as file:
            data = yaml.safe_load(file)
            print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: YAML file successfully loaded.")
    except FileNotFoundError:
        print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: File {filename} not found. Please ensure it exists in the current directory.")
        exit()
    except Exception as e:
        print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: An error occurred while loading the YAML file: {e}")
        exit()

    # Extract connectors
    connectors = data.get("connectors", {})

    # Determine all unique attributes across connectors
    all_keys = set()
    for connector in connectors.values():
        all_keys.update(connector.keys())

    # Create output directory if it doesn't exist
    output_directory = join(os.getcwd(), "support-do-not-edit")
    os.makedirs(output_directory, exist_ok=True)

    # Create a TSV file in the output directory
    tsv_filename = join(output_directory, f"{pn_from_dir()}-connector-list.tsv")
    try:
        with open(tsv_filename, mode='w', newline='') as tsv_file:
            writer = csv.DictWriter(tsv_file, fieldnames=["connector"] + list(all_keys), delimiter='\t')
            writer.writeheader()

            for connector_name, connector_attributes in connectors.items():
                row = {"connector": connector_name}
                row.update(connector_attributes)
                writer.writerow(row)

        print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: TSV file '{tsv_filename}' successfully created in '{output_directory}'.")
    except Exception as e:
        print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: An error occurred while creating the TSV file: {e}")

if __name__ == "__main__":
    generate_connector_list()
