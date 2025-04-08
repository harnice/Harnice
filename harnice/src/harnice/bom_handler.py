import os
import csv
from os.path import basename, join
from inspect import currentframe
import utils
import file



"""consider adding this:
        if "MPN" not in header:
            print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: 'MPN' column not found in the BOM file.")
            return
        mpn_index = header.index("MPN")
        if "Id" not in header:
            print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: 'MPN' column not found in the BOM file.")
            return
"""

def process_boms():
    combine_tsv_boms()
    add_description_simple_to_harness_bom()
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
    with open(filepath("harness bom"), mode='w', newline='', encoding='utf-8') as tsvfile:
        writer = csv.DictWriter(tsvfile, fieldnames=all_columns, delimiter='\t')
        writer.writeheader()
        for row in combined_data:
            # Fill in missing columns with empty strings
            complete_row = {col: row.get(col, '') for col in all_columns}
            writer.writerow(complete_row)

#def add_lengths_to_harness_bom():

def add_description_simple_to_harness_bom():
    """
    Opens, reads, processes, and writes back a TSV file by adding a "Description Simple" column next to the "Description" column.
    The new column is populated based on a dictionary of substitutions that can be expanded as needed.
    
    :param filepath: Path to the TSV file to be processed.
    """
    substitutions = {
        "Cable": "Cable",
        "Connector": "Connector",
        "Backshell": "Backshell",
    }
    
    with open(filepath("harness bom"), mode='r', encoding='utf-8') as tsvfile:
        lines = [line.strip().split('\t') for line in tsvfile.readlines()]
    
    header = lines[0]
    if "Description" in header:
        desc_index = header.index("Description")
        header.insert(desc_index + 1, "Description Simple")
    
        for row in lines[1:]:
            description = row[desc_index] if desc_index < len(row) else ""
            simple_desc = ""
            for key, value in substitutions.items():
                if key in description:
                    simple_desc = value
                    break
            row.insert(desc_index + 1, simple_desc)
    
    with open(filepath("harness bom"), mode='w', newline='', encoding='utf-8') as tsvfile:
        for row in lines:
            tsvfile.write('\t'.join(row) + '\n')
