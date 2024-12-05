
import os
import re
import datetime
import json
from os.path import basename
from inspect import currentframe

pn = None
rev = None

def generate_revision_history_tsv(filename):
    """
    Creates and saves a TSV file named {pn}-revision-history.tsv in the parent directory.

    :param pn: The prefix to use in the file name.
    """
    # Get the parent directory path
    parent_dir = os.path.dirname(os.getcwd())

    # Construct the file path
    file_path = os.path.join(parent_dir, f"{pn}-revision-history.tsv")

    # Define the columns for the TSV file
    columns = ["pn", "desc", "rev", "status", "releaseticket", "datestarted", "datemodified", "datereleased", "drawnby", "checkedby", "revisionupdates"]

    # Write the TSV file
    with open(file_path, 'w') as file:
        file.write('\t'.join(columns) + '\n')
    
    print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: New {pn}-revision-history document added to parent PN directory.")

def check_directory_format():
    """
    Checks if the current directory has the format {wildcard}-rev{number}.
    If true, sets global variables 'pn' and 'rev' and returns True.
    Otherwise, returns False.

    :return: True if the format matches, otherwise False
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
        check_subdirectory_format()
        return False

def check_subdirectory_format():
    """
    Checks if the current directory contains a subdirectory with the name {wildcard}-rev{number}.
    Outputs 'true' if such a subdirectory exists, otherwise 'false'.
    """
    # Get the current directory name and list its subdirectories
    current_dir = os.getcwd()
    subdirectories = [d for d in os.listdir(current_dir) if os.path.isdir(os.path.join(current_dir, d))]

    # Define the regex pattern for the format {wildcard}-rev{number}
    pattern = r"^(.*)-rev(\d+)$"

    subdirs_checked = 0
    subdirs_matched = 0
    for subdir in subdirectories:
        subdirs_checked += 1
        # Match the pattern against the subdirectory name
        match = re.match(pattern, subdir)
        if match:
            subdirs_matched += 1
    
    if subdirs_checked == 0:
        #no subdirectories found
        print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: If you're currently in a PN directory, create a rev directory inside here. Read documentation on harnice file structure!")
    if subdirs_checked > 0:
        if(subdirs_matched == 0):
            #subdirectories found, but none match
            print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: If you're currently in a PN directory, create a rev directory inside here. Read documentation on harnice file structure!")
        else:
            #subdirectories found, at least one matches
            print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Please navigate to a valid rev folder inside this one!")

def check_existence_of_rev_history_file_in_parent(pn):
    """
    Checks if the parent directory contains a file named {pn}-revision-history.tsv.

    :param pn: The prefix to check in the file name.
    :return: True if the file exists in the parent directory, otherwise False.
    """
    # Get the parent directory path
    parent_dir = os.path.dirname(os.getcwd())

    # Construct the expected file name
    expected_file = f"{pn}-revision-history.tsv"

    # Check if the file exists in the parent directory
    file_path = os.path.join(parent_dir, expected_file)
    if os.path.isfile(file_path):
        print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: {pn}-revision-history.tsv exists.")
        return True
    else:
        generate_revision_history_tsv(f"{pn}-revision-history.tsv")
        return True

def find_pn_and_rev_entry_in_tsv():
    """
    Looks for a row in the TSV file named {pn}-revision-history.tsv in the parent directory
    where the "PN" column matches the global 'pn' value and the "Rev" column matches the global 'rev' value.

    :return: True if the row is found, False otherwise.
    """

    # Construct the file path in the parent directory
    parent_dir = os.path.dirname(os.getcwd())
    file_path = os.path.join(parent_dir, f"{pn}-revision-history.tsv")

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

            # Iterate through the rows to find a match
            num_matching_rev_records = 0
            for line in file:
                row = line.strip().split('\t')
                if (
                    row[pn_index] == str(pn)
                    and row[rev_index] == str(rev)
                    ):
                    num_matching_rev_records += 1
            if num_matching_rev_records == 0:
                print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Revision record not found in {pn}-revision-history.tsv. Generating now.")
                add_initial_release_row_to_existing_tsv()
                return True
            
            if num_matching_rev_records == 1:
                print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Revision record identified. ")
                return True

            if num_matching_rev_records > 1:
                print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Duplicate revision entries in {pn}-revision-history.tsv. Please fix this document before continuing. ")
                return False


    except Exception as e:
        print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: An error occurred: {e}")
        return False

def add_initial_release_row_to_existing_tsv():
    """
    Adds a singular row to an existing TSV file named {pn}-revision-history.tsv in the parent directory.
    The row will include only the specific values for "PN", "Rev", and "Revision Updates" without repeating headers.
    """

    # Get the parent directory path
    parent_dir = os.path.dirname(os.getcwd())

    # Construct the file path
    file_path = os.path.join(parent_dir, f"{pn}-revision-history.tsv")

    # Construct the row values
    today_date = datetime.date.today().isoformat()
    row_values = [pn, "", rev, "", "", today_date, "", "", "", "", "Initial Release"]  # Only specific columns filled
    row = '\t'.join(map(str, row_values)) + '\n'

    # Append the row to the file
    with open(file_path, 'a') as file:
        file.write(row)

    print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Revision record added to {pn}-revision-history.tsv")

def check_revision_status():

    # Construct the file path in the parent directory
    parent_dir = os.path.dirname(os.getcwd())
    file_path = os.path.join(parent_dir, f"{pn}-revision-history.tsv")

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

def export_rev_row_from_tsv_to_project_rev_json():
    # Get the parent directory path
    parent_dir = os.path.dirname(os.getcwd())
    tsv_file_path = os.path.join(parent_dir, f"{pn}-revision-history.tsv")

    # Directory and file path for JSON
    json_dir = os.path.join(os.getcwd(), "support-do-not-edit")
    os.makedirs(json_dir, exist_ok=True)
    json_file_path = os.path.join(json_dir, f"{pn}-rev{rev}-tblock-master-text.json")

    if not os.path.isfile(tsv_file_path):
        print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: File {pn}-revision-history.tsv not found.")
        return

    try:
        with open(tsv_file_path, 'r') as file:
            header = file.readline().strip().split('\t')  # Read and split header
            for line in file:
                row = line.strip().split('\t')  # Read and split row
                if len(row) == len(header) and \
                   row[header.index("pn")] == pn and str(row[header.index("rev")]) == str(rev):
                    
                    # Create a JSON object with all fields, without placing quotes around values
                    json_data = {header[i]: eval(row[i]) if row[i].isdigit() else row[i] for i in range(len(header))}

                    # Overwrite JSON file
                    with open(json_file_path, 'w') as json_file:
                        json.dump(json_data, json_file, indent=4, separators=(',', ': '), ensure_ascii=False)

                    print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Revision data updated from {pn}-revision-history.tsv into {pn}-rev{rev}-tblock-master-text.json")
                    return

        print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Matching row not found in the TSV file.")

    except Exception as e:
        print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: An error occurred: {e}")

def harnice_prechecker():
    if check_directory_format() == False:
        return False
    print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: You're in a valid directory.")
    check_existence_of_rev_history_file_in_parent(pn)
    find_pn_and_rev_entry_in_tsv()
    if check_revision_status() == False:
        return False
    print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Status for this rev is clear; moving forward.")
    export_rev_row_from_tsv_to_project_rev_json()
    return True
    

if __name__ == "__main__":
    harnice_prechecker()