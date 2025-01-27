import os
import csv
from os.path import basename, join
from inspect import currentframe
from utility import *

def process_boms():
    combine_tsv_boms()
    #add_lengths_to_harness_bom()
    #generate_printable_bom()
    #generate_printable_wirelist()

def combine_tsv_boms():
    """
    Combines specific TSV files, merging columns with the same header
    and adding new columns for unmatched headers, without using pandas.
    """

    # Define the input file paths
    input_files = [
        filepath("electrical bom"),
        filepath("mechanical bom"),
        filepath("wirelist lengths"),
    ]
    
    # Initialize data structures
    combined_data = []
    all_columns = []

    #TO-DO: ADD A CLAUSE THAT COPIES DESCRIPTION INTO MPN FIELDS IF MPN IS BLANK

    # Process each file
    for file in input_files:
        if os.path.exists(file):
            print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Processing {file}...")
            with open(file, mode='r', newline='', encoding='utf-8') as tsvfile:
                reader = csv.DictReader(tsvfile, delimiter='\t')
                # Add new columns to the master list if not already present
                for column in reader.fieldnames:
                    if column not in all_columns:
                        all_columns.append(column)
                # Add rows of data
                for row in reader:
                    combined_data.append(row)
        else:
            print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Warning: {file} not found. Skipping.")

    if not combined_data:
        print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: No files were combined. Exiting.")
        return

    # Write the combined data to the output file
    print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Writing combined data to {filepath("harness bom")}...")
    with open(filepath("harness bom"), mode='w', newline='', encoding='utf-8') as tsvfile:
        writer = csv.DictWriter(tsvfile, fieldnames=all_columns, delimiter='\t')
        writer.writeheader()
        for row in combined_data:
            # Fill in missing columns with empty strings
            complete_row = {col: row.get(col, '') for col in all_columns}
            writer.writerow(complete_row)

    print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Combined TSV file saved to {filepath("harness bom")}")

#def add_lengths_to_harness_bom():


# Run the function
if __name__ == "__main__":
    combine_tsv_boms()
