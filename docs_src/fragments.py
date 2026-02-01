import docs_compiler
from harnice.products import harness, system

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
path = docs_compiler.harnice_dir() / "docs" / "fragments" / "_harness_default_feature_tree.md"
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
path = docs_compiler.harnice_dir() / "docs" / "fragments" / "_system_default_feature_tree.md"
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text("".join(md), encoding="utf-8")