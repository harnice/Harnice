"""
build_feature_tree_gui.py
Introspects harnice modules and generates function_index.json for the
Harnice console dropdowns. Run once after install or module changes.

Uses feature_tree_spec.py for organization and to determine which functions
to scrape. Organization is manual and independent of source code layout.

Usage:
    python build_feature_tree_gui.py
from src/harnice/gui/ or any location — it resolves paths relative to itself.
"""

import ast
import json
from pathlib import Path

from harnice.gui.feature_tree_spec import FEATURE_TREE_SPEC, MODULE_PATHS

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

_HARNICE_ROOT = Path(__file__).resolve().parents[1]  # src/harnice/
_OUTPUT = Path(__file__).resolve().parent / "function_index.json"

# ---------------------------------------------------------------------------
# Spec helpers
# ---------------------------------------------------------------------------


def _collect_function_refs(spec_node) -> set:
    """Recursively collect all (module, function) pairs from spec."""
    refs = set()
    if isinstance(spec_node, dict):
        for child in spec_node.values():
            refs.update(_collect_function_refs(child))
    elif isinstance(spec_node, list):
        for item in spec_node:
            if isinstance(item, tuple) and len(item) == 2:
                refs.add((item[0], item[1]))
    return refs


def _build_output_tree(spec_node, fn_lookup: dict) -> dict | list:
    """Build output structure with inlined metadata. fn_lookup key = (module, function)."""
    if isinstance(spec_node, dict):
        return {
            label: _build_output_tree(child, fn_lookup)
            for label, child in spec_node.items()
        }
    elif isinstance(spec_node, list):
        result = []
        for item in spec_node:
            if isinstance(item, tuple) and len(item) == 2:
                mod, fn = item
                if (mod, fn) in fn_lookup:
                    result.append(fn_lookup[(mod, fn)])
        return result
    return spec_node


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
    "str": '""',
    "int": "0",
    "float": "0.0",
    "bool": "False",
    "list": "[]",
    "dict": "{}",
    "List": "[]",
    "Dict": "{}",
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


def _parse_file(path: Path, module_alias: str, wanted_functions: set = None) -> list:
    """Parse file and return descriptors for requested functions. wanted_functions is set of (module, fn_name)."""
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
        results.append(node)

    # Identify top-level function nodes (direct children of Module)
    top_level = {
        n for n in ast.iter_child_nodes(tree) if isinstance(n, ast.FunctionDef)
    }

    functions = []
    for node in top_level:
        name = node.name
        if name.startswith("_"):
            continue  # skip private

        # Only include if in wanted set (or None = all). wanted_functions is set of fn names for this module.
        if wanted_functions is not None and name not in wanted_functions:
            continue

        # Docstring
        docstring = None
        if (
            node.body
            and isinstance(node.body[0], ast.Expr)
            and isinstance(node.body[0].value, ast.Constant)
            and isinstance(node.body[0].value.value, str)
        ):
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
            placeholder = (
                default if default is not None else _placeholder_from_annotation(ann)
            )
            args_out.append(
                {
                    "name": arg.arg,
                    "annotation": ann,
                    "default": default,
                    "placeholder": placeholder,
                }
            )

        # *args
        if all_args.vararg:
            a = all_args.vararg
            ann = _annotation_str(a.annotation)
            args_out.append(
                {
                    "name": f"*{a.arg}",
                    "annotation": ann,
                    "default": None,
                    "placeholder": "[]",
                    "variadic": True,
                }
            )

        # **kwargs
        if all_args.kwarg:
            a = all_args.kwarg
            ann = _annotation_str(a.annotation)
            args_out.append(
                {
                    "name": f"**{a.arg}",
                    "annotation": ann,
                    "default": None,
                    "placeholder": "{}",
                    "variadic": True,
                }
            )

        # keyword-only args (after *)
        n_kw = len(all_args.kwonlyargs)
        n_kw_defaults = len(all_args.kw_defaults)
        kw_defaults_padded = [None] * (n_kw - n_kw_defaults) + list(
            all_args.kw_defaults
        )
        for i, arg in enumerate(all_args.kwonlyargs):
            ann = _annotation_str(arg.annotation)
            default_node = kw_defaults_padded[i]
            default = _default_str(default_node)
            placeholder = (
                default if default is not None else _placeholder_from_annotation(ann)
            )
            args_out.append(
                {
                    "name": arg.arg,
                    "annotation": ann,
                    "default": default,
                    "placeholder": placeholder,
                    "keyword_only": True,
                }
            )

        functions.append(
            {
                "module": module_alias,
                "function": name,
                "docstring": docstring,
                "args": args_out,
            }
        )

    functions.sort(key=lambda f: f["function"])
    return functions


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def build():
    refs = _collect_function_refs(FEATURE_TREE_SPEC)
    modules_needed = {mod for mod, _ in refs}

    fn_lookup = {}
    for mod in sorted(modules_needed):
        if mod not in MODULE_PATHS:
            print(f"  [skip] unknown module in spec: {mod}")
            continue
        rel_path = MODULE_PATHS[mod]
        path = _HARNICE_ROOT / rel_path
        wanted = {
            fn for m, fn in refs if m == mod
        }  # set of function names for this module
        print(f"Parsing {mod} ({path.name})...")
        fns = _parse_file(path, mod, wanted_functions=wanted)
        print(f"  {len(fns)} functions found")
        for fn in fns:
            fn_lookup[(fn["module"], fn["function"])] = fn

    missing = refs - set(fn_lookup.keys())
    if missing:
        for mod, fn in sorted(missing):
            print(f"  [warn] not found in source: {mod}.{fn}")

    output_tree = _build_output_tree(FEATURE_TREE_SPEC, fn_lookup)
    _OUTPUT.write_text(json.dumps(output_tree, indent=2), encoding="utf-8")
    print(f"\nWrote function index to {_OUTPUT}")


if __name__ == "__main__":
    build()
