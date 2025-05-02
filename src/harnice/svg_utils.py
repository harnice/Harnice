import os
import json
import re
import csv
import shutil
from os.path import basename
from inspect import currentframe
import fileio
import component_library

def new_blank_svg(filepath, groupname):
    # Delete the file if it exists
    if os.path.exists(filepath):
        os.remove(filepath)

    # Create a blank SVG with two named groups
    with open(filepath, 'w') as f:
        f.write(
            '<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n'
            '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="1000" height="1000">\n'
            f'  <g id="{groupname}-contents-start" />\n'
            f'  <g id="{groupname}-contents-end" />\n'
            '</svg>\n'
        )

def add_entire_svg_file_contents_to_group(filepath, new_group_name):
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as file:
                svg_content = file.read()

            match = re.search(r'<svg[^>]*>(.*?)</svg>', svg_content, re.DOTALL)
            if not match:
                raise ValueError("File does not appear to be a valid SVG or has no inner contents.")
            inner_content = match.group(1).strip()

            updated_svg_content = (
                f'<svg xmlns="http://www.w3.org/2000/svg">\n'
                f'  <g id="{new_group_name}-contents-start">\n'
                f'    {inner_content}\n'
                f'  </g>\n'
                f'  <g id="{new_group_name}-contents-end"></g>\n'
                f'</svg>\n'
            )

            with open(filepath, "w", encoding="utf-8") as file:
                file.write(updated_svg_content)

            print(
                f"from {basename(__file__)} > {currentframe().f_code.co_name}: "
                f"Added entire contents of {os.path.basename(filepath)} to a new group {new_group_name}-contents-start"
            )
        except Exception as e:
            print(
                f"from {basename(__file__)} > {currentframe().f_code.co_name}: "
                f"Error adding contents of {os.path.basename(filepath)} to a new group {new_group_name}: {e}"
            )
    else:
        print(
            f"from {basename(__file__)} > {currentframe().f_code.co_name}: "
            f"Trying to add contents of {os.path.basename(filepath)} to a new group but file does not exist."
        )


def find_and_replace_svg_group(target_svg_filepath, source_svg_filepath, group_id):
    try:
        with open(source_svg_filepath, 'r') as source_file:
            source_svg_content = source_file.read()
        with open(target_svg_filepath, 'r') as target_file:
            target_svg_content = target_file.read()

        start_tag = f'id="{group_id}-contents-start"'
        end_tag = f'id="{group_id}-contents-end"'
        success = 0

        source_start_index = source_svg_content.find(start_tag)
        if source_start_index == -1:
            print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Source start tag <{start_tag}> not found in <{fileio.name(source_svg_filepath)}>.")
            return success
        source_end_index = source_svg_content.find(end_tag)
        if source_end_index == -1:
            print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Source end tag <{end_tag}> not found in <{fileio.name(source_svg_filepath)}>.")
            return success

        target_start_index = target_svg_content.find(start_tag)
        if target_start_index == -1:
            print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Target start tag <{start_tag}> not found in <{fileio.name(target_svg_filepath)}>.")
            return success
        target_end_index = target_svg_content.find(end_tag)
        if target_end_index == -1:
            print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Target end tag <{end_tag}> not found in <{fileio.name(target_svg_filepath)}>.")
            return success

        replacement_group_content = source_svg_content[source_start_index:source_end_index]
        updated_svg_content = (
            target_svg_content[:target_start_index]
            + replacement_group_content
            + target_svg_content[target_end_index:]
        )

        try:
            with open(target_svg_filepath, 'w') as updated_file:
                updated_file.write(updated_svg_content)
        except Exception as e:
            print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Error writing to <{fileio.name(target_svg_filepath)}>: {e}")
            return success

        print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Copied group <{group_id}> from <{fileio.name(source_svg_filepath)}> to <{fileio.name(target_svg_filepath)}>.")
        success = 1

    except Exception as e:
        print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Error processing files <{fileio.name(source_svg_filepath)}> and <{fileio.name(target_svg_filepath)}>: {e}")
    return success


def rotate_svg_group(svg_path, group_name, angle):
    id_string = f'id="{group_name}-contents-start"'
    try:
        with open(svg_path, 'r', encoding='utf-8') as svg_file:
            lines = svg_file.readlines()

        group_found = False
        for i, line in enumerate(lines):
            if id_string in line:
                if 'transform="rotate(' in line:
                    lines[i] = re.sub(r'rotate\(([^)]+)\)', f'rotate({angle})', line)
                else:
                    lines[i] = line.strip().replace('>', f' transform="rotate({angle})">') + '\n'
                group_found = True
                break

        if not group_found:
            raise ValueError(f"{group_name} group not initialized correctly.")

        with open(svg_path, 'w', encoding='utf-8') as svg_file:
            svg_file.writelines(lines)

        print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Rotated {group_name} to {angle} deg in {os.path.basename(svg_path)}.")
    except FileNotFoundError:
        print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: File not found - {svg_path}")
    except ValueError as e:
        print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Error: {e}")
    except Exception as e:
        print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Unexpected error: {e}")


def pull_tblock_info_from_json():
    with open(fileio.path("tblock master text"), 'r') as jf:
        return json.load(jf)


def prep_tblock_svg_master():
    json_tblock_data = pull_tblock_info_from_json()

    wanted_tblock_libdomain = "rs"
    wanted_tblock_libsubpath = "page_defaults"
    wanted_tblock_libfilename = "rs-tblock-default.svg"
    library_used_tblock_filepath = os.path.join(os.getcwd(), "editable_component_data", wanted_tblock_libsubpath, wanted_tblock_libfilename)

    component_library.import_library_file(wanted_tblock_libdomain, wanted_tblock_libsubpath, wanted_tblock_libfilename)

    if os.path.exists(fileio.path("tblock master svg")):
        os.remove(fileio.path("tblock master svg"))

    shutil.copy(library_used_tblock_filepath, fileio.dirpath("master_svgs"))
    os.rename(
        os.path.join(fileio.dirpath("master_svgs"), wanted_tblock_libfilename),
        fileio.path("tblock master svg")
    )

    with open(fileio.path("tblock master svg"), 'r') as inf:
        content = inf.read()

    def replacer(match):
        key = match.group(1)
        old_text = match.group(0)
        new_text = str(json_tblock_data.get(key, old_text))
        print(f"Replacing: '{old_text}' with: '{new_text}'")
        return new_text

    updated_content = re.sub(r"tblock-key-(\w+)", replacer, content)

    with open(fileio.path("tblock master svg"), 'w') as inf:
        inf.write(updated_content)
        print("Updated tblock info.")


def read_tsv(file_path, columns, numeric_filter_column):
    with open(file_path, 'r', newline='', encoding='utf-8') as tsv_file:
        reader = csv.DictReader(tsv_file, delimiter='\t')
        return [
            [row[col] for col in columns]
            for row in reader if row[numeric_filter_column].isdigit()
        ]


def regen_harnice_output_svg():
    svg_utils.find_and_replace_svg_group(fileio.path("harnice output"), fileio.path("formboard master svg"), "formboard-master")
    print()
    svg_utils.find_and_replace_svg_group(fileio.path("harnice output"), fileio.path("bom table master svg"), "bom-master")
    print()
    svg_utils.find_and_replace_svg_group(fileio.path("harnice output"), fileio.path("revhistory master svg"), "revision-history-master")
    print()
    svg_utils.find_and_replace_svg_group(fileio.path("harnice output"), fileio.path("tblock master svg"), "tblock-master")
    print()
    svg_utils.find_and_replace_svg_group(fileio.path("harnice output"), fileio.path("buildnotes master svg"), "buildnotes-master")
    print()
    svg_utils.find_and_replace_svg_group(fileio.path("harnice output"), fileio.path("esch master svg"), "esch-master")
    print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: No more replacements.")
