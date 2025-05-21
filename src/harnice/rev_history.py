import os
import re
import datetime
import json
import csv
from os.path import basename, dirname
from inspect import currentframe
from harnice import (
    fileio,
    cli
)

"""
def harnice_prechecker():
    if check_directory_format() == False:
        return False
    print(f"You're working in a valid directory (revision of a part).")
    check_existence_of_rev_history_file_in_parent(pn)
    find_rev_entry_in_tsv()
    if check_revision_status() == False:
        raise RuntimeError("Harnice is not allowed to operate on revisions with any value in the 'status' column of the revision history sheet to protect version control.")
    print(f"Status for this rev is clear; moving forward.")


def pn_from_cwd():
    check_directory_format()
    return pn

def rev_from_cwd():
    check_directory_format()
    return rev

def check_directory_format():
    """
    #Checks if the current directory has the format {wildcard}-rev{number}.
    #If true, sets global variables 'pn' and 'rev' and returns True.
    #Otherwise, returns False.

    #:return: True if the format matches, otherwise False
"""
    global pn, rev

    # Get the current directory name
    current_dir = os.path.basename(os.getcwd())

    # Define the regex pattern for the format {wildcard}-rev{number}
    pattern = r"^(.*)-rev(\d+)$"

    # Match the pattern against the current directory name
    match = re.match(pattern, current_dir)

    if match:
        # Extract {wildcard} and {number}
        pn = match.group(1)
        rev = int(match.group(2))
        return True
    else:
        check_subdirectory_format(os.get.cwd())
        return False"""

def generate_revision_history_tsv():
    # Define the columns for the TSV file
    columns = [
        "pn", 
        "desc", 
        "rev", 
        "status", 
        "releaseticket", 
        "datestarted", 
        "datemodified", 
        "datereleased", 
        "drawnby", 
        "checkedby", 
        "revisionupdates", 
        "affectedinstances"
        ]

    # Write the TSV file
    with open(fileio.path("revision history"), 'w') as file:
        file.write('\t'.join(columns) + '\n')

def check_existence_of_rev_history_file_in_parent(pn):
    file_path = fileio.path("revision history")
    if os.path.isfile(file_path):
        return True
    else:
        generate_revision_history_tsv()
        return True

def find_rev_entry_in_tsv(rev):
    """
    Looks for a row in the TSV file named {pn}-revision_history.tsv in the parent directory
    where the "PN" column matches the global 'pn' value and the "Rev" column matches the global 'rev' value.

    :return: True if the row is found, False otherwise.
    """

    # Construct the file path in the parent directory
    file_path = fileio.path("revision history")

    with open(file_path, 'r') as file:
        # Read the header to identify the column indices for "PN" and "Rev"
        header = file.readline().strip().split('\t')
        if "pn" not in header or "rev" not in header:
            raise(f"'PN' or 'Rev' column not found in the file.")

        # Get the indices of the "PN" and "Rev" columns
        pn_index = header.index("pn")
        rev_index = header.index("rev")

        # Iterate through the rows to find a match
        num_matching_rev_records = 0
        for line in file:
            row = line.strip().split('\t')
            if (
                row[pn_index] == str(fileio.partnumber("pn"))
                and row[rev_index] == str(rev)
                ):
                num_matching_rev_records += 1
        if num_matching_rev_records == 0:
            return False
        
        if num_matching_rev_records == 1:
            return True

        if num_matching_rev_records > 1:
            raise(f"Duplicate revision entries in {pn}-revision_history.tsv in the parent directory. Please fix this before continuing. ")

def append_new_row(rev, message):
    """
    Adds a singular row to an existing TSV file named {pn}-revision_history.tsv in the parent directory.
    The row will include only the specific values for "PN", "Rev", and "Revision Updates" without repeating headers.
    """
    pn = fileio.partnumber("pn")

    # Construct the row values
    today_date = datetime.date.today().isoformat()
    row_values = [pn, "", rev, "", "", today_date, "", "", "", "", message]  # Only specific columns filled
    row = '\t'.join(map(str, row_values)) + '\n'

    # Append the row to the file
    with open(fileio.path("revision history"), 'a') as file:
        file.write(row)

def check_revision_status():
    # Construct the file path in the parent directory
    file_path = fileio.path("revision history")

    try:
        with open(file_path, 'r') as file:
            # Read the header to identify the column indices for "PN" and "Rev"
            header = file.readline().strip().split('\t')
            if "pn" not in header or "rev" not in header:
                print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: 'PN' or 'Rev' column not found in the file.")
                return False

            # Get the indices of the "PN" and "Rev" columns
            pn_index = header.index("pn")
            rev_index = header.index("rev")
            status_index = header.index("status")

            # Iterate through the rows to find a match
            for line in file:
                row = line.strip().split('\t')
                if (
                    row[pn_index] == str(pn)
                    and row[rev_index] == str(rev)
                    ):
                    if (row[status_index] == ""):
                        return True
                    else:
                        print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Status for this rev: {row[status_index]}")
                        print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Either change the status or work on a new revision. Aborting harnice.")
                        return False


    except Exception as e:
        print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: An error occurred: {e}")
        return False

def revision_info():
    rev_path = fileio.path("revision history")
    if not os.path.exists(rev_path):
        raise FileNotFoundError(f"[ERROR] Revision history file not found: {rev_path}")

    with open(rev_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            if row.get("rev") == fileio.partnumber("R"):
                return {k: (v or "").strip() for k, v in row.items()}

    raise ValueError(f"[ERROR] No revision row found for rev '{fileio.partnumber('R')}' in revision history")



