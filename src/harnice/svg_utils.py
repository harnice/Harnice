import os
import json
import re
import csv
import shutil
from os.path import basename
from inspect import currentframe
import fileio
import component_library

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


def find_and_replace_svg_group(target_svg_filepath, source_svg_filepath, source_group_name, destination_group_name):
    try:
        with open(source_svg_filepath, 'r') as source_file:
            source_svg_content = source_file.read()
        with open(target_svg_filepath, 'r') as target_file:
            target_svg_content = target_file.read()

        source_start_tag = f'id="{source_group_name}-contents-start"'
        source_end_tag = f'id="{source_group_name}-contents-end"'
        dest_start_tag = f'id="{destination_group_name}-contents-start"'
        dest_end_tag = f'id="{destination_group_name}-contents-end"'
        success = 0

        source_start_index = source_svg_content.find(source_start_tag)
        if source_start_index == -1:
            print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Source start tag <{source_start_tag}> not found in <{source_svg_filepath}>.")
            return success
        source_end_index = source_svg_content.find(source_end_tag)
        if source_end_index == -1:
            print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Source end tag <{source_end_tag}> not found in <{source_svg_filepath}>.")
            return success

        dest_start_index = target_svg_content.find(dest_start_tag)
        if dest_start_index == -1:
            print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Target start tag <{dest_start_tag}> not found in <{target_svg_filepath}>.")
            return success
        dest_end_index = target_svg_content.find(dest_end_tag)
        if dest_end_index == -1:
            print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Target end tag <{dest_end_tag}> not found in <{target_svg_filepath}>.")
            return success

        replacement_group_content = source_svg_content[source_start_index:source_end_index]
        updated_svg_content = (
            target_svg_content[:dest_start_index]
            + replacement_group_content
            + target_svg_content[dest_end_index:]
        )

        try:
            with open(target_svg_filepath, 'w') as updated_file:
                updated_file.write(updated_svg_content)
        except Exception as e:
            print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Error writing to <{target_svg_filepath}>: {e}")
            return success

        print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Replaced group <{destination_group_name}> with <{source_group_name}> from <{source_svg_filepath}> to <{target_svg_filepath}>.")
        success = 1

    except Exception as e:
        print(f"from {basename(__file__)} > {currentframe().f_code.co_name}: Error processing files <{source_svg_filepath}> and <{target_svg_filepath}>: {e}")
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
