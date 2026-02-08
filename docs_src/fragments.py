import docs_functions
from harnice.products import harness, system, cable
from harnice.utils import circuit_utils
from harnice.lists import channel_map, signals_list

def main():
    #========================================================
    # HARNESS DEFAULT FEATURE TREE
    #========================================================
    module_prefix = "harness_default_feature_tree"

    md = ['''??? note "Default harness feature tree"\n    ```python''']

    feature_tree = harness._make_feature_tree(
        harness.default_build_macro_block(
            "system_part_number",
            "system_revision",
            "target_net"
        ),
        push_block=harness.default_push_block()
    )

    for line in feature_tree.split("\n"):
        md.append("\n    " + line)

    md.append("```")
    path = docs_functions.harnice_dir() / "docs" / "fragments" / "_harness_default_feature_tree.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(md), encoding="utf-8")

    #========================================================
    # SYSTEM DEFAULT FEATURE TREE
    #========================================================
    module_prefix = "system_default_feature_tree"

    md = ['''??? note "Default system feature tree "\n    ```python''']

    feature_tree = system.system_feature_tree_utils_default

    for line in feature_tree.split("\n"):
        md.append("\n    " + line)

    md.append("```")
    path = docs_functions.harnice_dir() / "docs" / "fragments" / "_system_default_feature_tree.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(md), encoding="utf-8")

    #========================================================
    # MAPPING VOCABULARY
    #========================================================
    module_prefix = "mapping_vocabulary"

    md = ['??? note "Mapping vocabulary"']

    md.append(f"\n\n    **Cable:**")
    md.append(f"\n\n    - {cable.documentation_description}\n\n")
    md.append(f"\n\n    **Conductor:**")
    md.append(f"\n\n    - {circuit_utils.conductor_documentation_description}\n\n")
    md.append(f"\n\n    **Circuit:**")
    md.append(f"\n\n    - {circuit_utils.circuit_documentation_description}\n\n")
    md.append(f"\n\n    **Channel:**")
    md.append(f"\n\n    - {channel_map.channel_documentation_description}\n\n")
    md.append(f"\n\n    **Net:**")
    md.append(f"\n\n    - A Kicad/eCad term that represents a common node of electrical signals. Used in Harnice to represent a physical harness build, that bounds connectors into one set.")
    md.append(f"\n\n    **Signal:**")
    md.append(f"\n\n    - {signals_list.signal_documentation_description}\n\n")

    path = docs_functions.harnice_dir() / "docs" / "fragments" / "_mapping_vocabulary.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(md), encoding="utf-8")