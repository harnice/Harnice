import os
import re

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

        except Exception as e:
            print(
                f"Error adding contents of {os.path.basename(filepath)} to a new group {new_group_name}: {e}"
            )
    else:
        print(
            f"Trying to add contents of {os.path.basename(filepath)} to a new group but file does not exist."
        )

def find_and_replace_svg_group(target_svg_filepath, source_svg_filepath, source_group_name, destination_group_name):
    with open(source_svg_filepath, 'r', encoding='utf-8') as source_file:
        source_svg_content = source_file.read()
    with open(target_svg_filepath, 'r', encoding='utf-8') as target_file:
        target_svg_content = target_file.read()

    source_start_tag = f'id="{source_group_name}-contents-start"'
    source_end_tag = f'id="{source_group_name}-contents-end"'
    dest_start_tag = f'id="{destination_group_name}-contents-start"'
    dest_end_tag = f'id="{destination_group_name}-contents-end"'

    source_start_index = source_svg_content.find(source_start_tag)
    if source_start_index == -1:
        raise ValueError(f"[ERROR] Source start tag <{source_start_tag}> not found in <{source_svg_filepath}>.")
    source_start_index = source_svg_content.find(">", source_start_index) + 1

    source_end_index = source_svg_content.find(source_end_tag)
    if source_end_index == -1:
        raise ValueError(f"[ERROR] Source end tag <{source_end_tag}> not found in <{source_svg_filepath}>.")
    source_end_index = source_svg_content.rfind("<", 0, source_end_index)

    dest_start_index = target_svg_content.find(dest_start_tag)
    if dest_start_index == -1:
        raise ValueError(f"[ERROR] Target start tag <{dest_start_tag}> not found in <{target_svg_filepath}>.")
    dest_start_index = target_svg_content.find(">", dest_start_index) + 1

    dest_end_index = target_svg_content.find(dest_end_tag)
    if dest_end_index == -1:
        raise ValueError(f"[ERROR] Target end tag <{dest_end_tag}> not found in <{target_svg_filepath}>.")
    dest_end_index = target_svg_content.rfind("<", 0, dest_end_index)

    replacement_group_content = source_svg_content[source_start_index:source_end_index]

    updated_svg_content = (
        target_svg_content[:dest_start_index]
        + replacement_group_content
        + target_svg_content[dest_end_index:]
    )

    with open(target_svg_filepath, 'w', encoding='utf-8') as updated_file:
        updated_file.write(updated_svg_content)

    return 1

