"""
build_feature_tree_gui.py
Introspects harnice modules and generates function_index.json for the
feature tree editor dropdowns. Run once after install or module changes.

Usage:
    python build_feature_tree_gui.py
from src/harnice/gui/ or any location — it resolves paths relative to itself.
"""

import ast
import json
from pathlib import Path

# ---------------------------------------------------------------------------
# Config: modules to introspect and their import aliases
# ---------------------------------------------------------------------------

_HARNICE_ROOT = Path(__file__).resolve().parents[1]  # src/harnice/

_TARGETS = [
    # (filesystem path relative to harnice root, import alias used in feature trees)
    ("lists/available_network.py",          "available_network"),
    ("lists/channel_map.py",                "channel_map"),
    ("lists/chosen_network.py",             "chosen_network"),
    ("lists/circuits_list.py",              "circuits_list"),
    ("lists/disconnect_map.py",             "disconnect_map"),
    ("lists/flattened_network.py",          "flattened_network"),
    ("lists/instances_list.py",             "instances_list"),
    ("lists/library_history.py",            "library_history"),
    ("lists/manifest.py",                   "manifest"),
    ("lists/post_harness_instances_list.py","post_harness_instances_list"),
    ("lists/rev_history.py",               "rev_history"),
    ("lists/signals_list.py",              "signals_list"),
    ("utils/appearance.py",                "appearance"),
    ("utils/circuit_utils.py",             "circuit_utils"),
    ("utils/feature_tree_utils.py",        "feature_tree_utils"),
    ("utils/library_utils.py",             "library_utils"),
    ("utils/note_utils.py",               "note_utils"),
    ("utils/svg_utils.py",                "svg_utils"),
    ("utils/system_utils.py",             "system_utils"),
    ("fileio.py",                          "fileio"),
    ("state.py",                           "state"),
]

_OUTPUT = Path(__file__).resolve().parent / "function_index.json"

# ---------------------------------------------------------------------------
# Type-hint annotation -> readable string
# ---------------------------------------------------------------------------

def _annotation_str(node) -> str:
    if node is None:
        return None
    if isinstance(node, ast.Constant):
        return repr(node.value)
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return f"{_annotation_str(node.value)}.{node.attr}"
    if isinstance(node, ast.Subscript):
        return f"{_annotation_str(node.value)}[{_annotation_str(node.slice)}]"
    if isinstance(node, ast.Tuple):
        return ", ".join(_annotation_str(e) for e in node.elts)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
        return f"{_annotation_str(node.left)} | {_annotation_str(node.right)}"
    try:
        return ast.unparse(node)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Default value -> Python literal string
# ---------------------------------------------------------------------------

def _default_str(node) -> str:
    if node is None:
        return None
    try:
        return ast.unparse(node)
    except Exception:
        return "None"


# ---------------------------------------------------------------------------
# Infer a placeholder value from annotation when no default exists
# ---------------------------------------------------------------------------

_ANNOTATION_PLACEHOLDERS = {
    "str":   '""',
    "int":   "0",
    "float": "0.0",
    "bool":  "False",
    "list":  "[]",
    "dict":  "{}",
    "List":  "[]",
    "Dict":  "{}",
    "tuple": "()",
    "Tuple": "()",
}

def _placeholder_from_annotation(ann: str) -> str:
    if ann is None:
        return "None"
    base = ann.split("[")[0].strip()
    return _ANNOTATION_PLACEHOLDERS.get(base, "None")


# ---------------------------------------------------------------------------
# Parse a single .py file -> list of function descriptors
# ---------------------------------------------------------------------------

def _parse_file(path: Path, module_alias: str) -> list:
    if not path.exists():
        print(f"  [skip] not found: {path}")
        return []

    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError as e:
        print(f"  [skip] syntax error in {path}: {e}")
        return []

    results = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        # Only top-level functions (parent is Module)
        # ast.walk doesn't track parents; we filter by checking depth via a
        # separate pass below. For now collect all and mark nested later.
        results.append(node)

    # Identify top-level function nodes (direct children of Module)
    top_level = {n for n in ast.iter_child_nodes(tree) if isinstance(n, ast.FunctionDef)}
    # Also include functions inside top-level classes if desired — skip for now.

    functions = []
    for node in top_level:
        name = node.name
        if name.startswith("_"):
            continue  # skip private

        # Docstring
        docstring = None
        if (node.body and isinstance(node.body[0], ast.Expr)
                and isinstance(node.body[0].value, ast.Constant)
                and isinstance(node.body[0].value.value, str)):
            docstring = node.body[0].value.value.strip().splitlines()[0]

        # Arguments — skip 'self' and 'cls'
        args_out = []
        all_args = node.args

        # Build defaults alignment: defaults align to the END of args list
        n_args = len(all_args.args)
        n_defaults = len(all_args.defaults)
        defaults_padded = [None] * (n_args - n_defaults) + list(all_args.defaults)

        for i, arg in enumerate(all_args.args):
            if arg.arg in ("self", "cls"):
                continue
            ann = _annotation_str(arg.annotation)
            default_node = defaults_padded[i]
            default = _default_str(default_node)
            placeholder = default if default is not None else _placeholder_from_annotation(ann)
            args_out.append({
                "name":        arg.arg,
                "annotation":  ann,
                "default":     default,
                "placeholder": placeholder,
            })

        # *args
        if all_args.vararg:
            a = all_args.vararg
            ann = _annotation_str(a.annotation)
            args_out.append({
                "name":        f"*{a.arg}",
                "annotation":  ann,
                "default":     None,
                "placeholder": "[]",
                "variadic":    True,
            })

        # **kwargs
        if all_args.kwarg:
            a = all_args.kwarg
            ann = _annotation_str(a.annotation)
            args_out.append({
                "name":        f"**{a.arg}",
                "annotation":  ann,
                "default":     None,
                "placeholder": "{}",
                "variadic":    True,
            })

        # keyword-only args (after *)
        n_kw = len(all_args.kwonlyargs)
        n_kw_defaults = len(all_args.kw_defaults)
        kw_defaults_padded = [None] * (n_kw - n_kw_defaults) + list(all_args.kw_defaults)
        for i, arg in enumerate(all_args.kwonlyargs):
            ann = _annotation_str(arg.annotation)
            default_node = kw_defaults_padded[i]
            default = _default_str(default_node)
            placeholder = default if default is not None else _placeholder_from_annotation(ann)
            args_out.append({
                "name":        arg.arg,
                "annotation":  ann,
                "default":     default,
                "placeholder": placeholder,
                "keyword_only": True,
            })

        functions.append({
            "module":    module_alias,
            "function":  name,
            "docstring": docstring,
            "args":      args_out,
        })

    functions.sort(key=lambda f: f["function"])
    return functions


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def build():
    index = []
    for rel_path, alias in _TARGETS:
        path = _HARNICE_ROOT / rel_path
        print(f"Parsing {alias} ({path.name})...")
        fns = _parse_file(path, alias)
        print(f"  {len(fns)} public functions found")
        index.extend(fns)

    _OUTPUT.write_text(json.dumps(index, indent=2), encoding="utf-8")
    print(f"\nWrote {len(index)} functions to {_OUTPUT}")


if __name__ == "__main__":
    build()