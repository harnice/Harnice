import os
import re
import datetime
import json
import csv
from os.path import basename
from inspect import currentframe
from harnice import (
    fileio
)

pn = None
rev = None

def harnice_prechecker():
    if check_directory_format() == False:
        return False
    print(f"You're working in a valid directory (revision of a part).")
    check_existence_of_rev_history_file_in_parent(pn)
    find_pn_and_rev_entry_in_tsv()
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
        check_subdirectory_format(os.get.cwd())
        return False

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
    
    print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: New {pn}-revision-history document added to parent PN directory.")

def check_subdirectory_format(dir_to_check):
    """
    Checks if the dir_to_check directory contains a subdirectory with the name {wildcard}-rev{number}.
    Raises a RuntimeError if no matching subdirectory is found.
    """

    subdirectories = [d for d in os.listdir(dir_to_check) if os.path.isdir(os.path.join(dir_to_check, d))]

    pattern = r"^(.*)-rev(\d+)$"

    subdirs_checked = 0
    subdirs_matched = 0
    for subdir in subdirectories:
        subdirs_checked += 1
        if re.match(pattern, subdir):
            subdirs_matched += 1

    src = f"from {basename(__file__)} > {currentframe().f_code.co_name}:"

    if subdirs_checked == 0:
        raise RuntimeError(f"{src} No subdirectories found. If you're currently in a PN directory, create a rev directory inside here. Read documentation on harnice file structure!")
    if subdirs_checked > 0 and subdirs_matched == 0:
        raise RuntimeError(f"{src} Subdirectories found, but none match '*-revX'. Create a proper rev directory. Read documentation on harnice file structure!")
    if subdirs_matched > 0:
        raise RuntimeError(f"{src} Please navigate to a valid rev folder (I see there is a valid one inside this one!)")

def check_existence_of_rev_history_file_in_parent(pn):
    file_path = fileio.path("revision history")
    if os.path.isfile(file_path):
        return True
    else:
        generate_revision_history_tsv()
        return True

def find_pn_and_rev_entry_in_tsv():
    """
    Looks for a row in the TSV file named {pn}-revision_history.tsv in the parent directory
    where the "PN" column matches the global 'pn' value and the "Rev" column matches the global 'rev' value.

    :return: True if the row is found, False otherwise.
    """

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
                print(f"Revision record not found in {pn}-revision_history.tsv. Adding now.")
                add_initial_release_row_to_existing_tsv()
                return True
            
            if num_matching_rev_records == 1:
                print(f"Record of this revision found in csv in parent directory.")
                return True

            if num_matching_rev_records > 1:
                print(f"Duplicate revision entries in {pn}-revision_history.tsv in the parent directory. Please fix this before continuing. ")
                return False


    except Exception as e:
        print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: An error occurred: {e}")
        return False

def add_initial_release_row_to_existing_tsv():
    """
    Adds a singular row to an existing TSV file named {pn}-revision_history.tsv in the parent directory.
    The row will include only the specific values for "PN", "Rev", and "Revision Updates" without repeating headers.
    """
    # Construct the file path
    file_path = fileio.path("revision history")

    # Construct the row values
    today_date = datetime.date.today().isoformat()
    row_values = [pn, "", rev, "", "", today_date, "", "", "", "", "Initial Release"]  # Only specific columns filled
    row = '\t'.join(map(str, row_values)) + '\n'

    # Append the row to the file
    with open(file_path, 'a') as file:
        file.write(row)

    print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Revision record added to {pn}-revision_history.tsv")

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



def verify_revision_structure():

    #first figure out where you are
    cwd_name = name(os.path.getcwd())
    cwd_path = os.path.getcwd()
    parent_dirname = use os to find parent dir
    parent_dirpath = use os to find parent dir path
    children_dir = [] use os to add the content files or directories of the cwd into this list
    part_path = ""
    rev_path = ""
    pn = ""
    rev = 0

    mode = "unknown"

    #if you're working in a part file, this must be true:
    if fr"{cwd_name}-rev*" in children_dir:
        mode = "partfile"
        part_path = cwd_path
        pn = cwd_name

    #if you're working in a revision file, this must be true:
    if cwd_name == fr"{parent_dir_name}-rev*":
        mode = "revisionfile"
        part_path = parent_dirpath
        rev_path = cwd
        pn = parent_dirname
        rev = cwd_name

    if mode == "unknown":
        print("Couldn't identify your file structure. Do you wish to create a new part out of this directory?")
        print(f"Part number: {cwd_name}")
        if cli.prompt(f"Hit enter to proceed or esc to terminate", default='y') == y:
            mode = "partfile"
            part_path = cwd_path
            pn = cwd_name

    #we should know at this point where the revision history file lives
    revhistory_tsv_filepath = os.path.join(part_path, f"{pn}.revisionhistory.tsv")
    #open it if it exists
    if os.exists(revhistory_tsv_filepath):
        open file at parent_dirpath with name f"{parent_dirname}.{revisionhistory}.tsv" 'r'
            revision_history_data = get
    #make a new rev1 line if doesn't exist
    else:
        today_date = datetime.date.today().isoformat()
        row_values = [pn, "", rev, "", "", today_date, "", "", "", "", "Initial Release"]  # Only specific columns filled
        row = '\t'.join(map(str, row_values)) + '\n'
        with open(revhistory_tsv_filepath, 'a') as file:
            file.write(row)
        rev = 1
        rev_path = os.path.join(part_path, f"{pn}-rev1")

    if mode == "partfile":
        for revision in revision_history_data:
            if revision.get("rev") > highest_rev:
                if revision.get("status") == "":
                    highest_unreleased_rev = revision.get("rev")

        if cli.prompt(f"Highest unreleased rev is {highest_unreleased_rev}. Hit to work on it, otherwise enter desired rev:", default = 'y') == y:
            rev_name = fr"{parent_dir_name}-rev{highest_unreleased_rev}"

    if mode == "revisionfile":
        if rev exists in any row of revision.get("rev") == :
            if not revision.get("status") == "":
                raise("Status for this rev is not blank. Harnice uses this column to version control parts. Either remove the text from that column (unrelease) or 'cd ..' and rerun to make a new rev")

    return mode, pn, rev

    