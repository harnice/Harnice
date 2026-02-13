# File I/O

The `fileio` module keeps files organized and easy to reference by name. Paths are resolved from a **file structure** that describes the layout of the current product’s revision folder.

## File structure

Products and macros define a **file structure** via a `file_structure()` function. It returns a nested dict that describes the layout of that product’s files **under the current revision directory** (the folder you’re in when you run the product).

- **Files**: each file is a key–value pair where the **key** is the filename and the **value** is a short, human-readable **file key** (e.g. `"myfile.tsv": "signals list"`). You use the file key with `fileio.path("signals list")`.
- **Directories**: a directory is a key whose **value** is another dict (empty `{}` or more key–value pairs). The **key** is the directory name and is what you pass to `fileio.dirpath("dirname")`.

You can add extra arguments to `file_structure()` (and pass a custom dict into fileio) for more complex layouts.

When you run a product, the CLI sets that product’s file structure as the default for fileio. After that, path lookups use the current product’s layout unless you override it.

## Integration with state

Fileio and the product file structure rely on **`state`** for the current context:

- **`state.pn`** — Current part number (e.g. `"mypart"`). Set by `fileio.verify_revision_structure()` from the current directory or when creating a new revision.
- **`state.rev`** — Current revision number (integer). Set at the same time as `state.pn`.
- **`state.partnumber(format)`** — Builds part/revision strings. Formats: `"pn-rev"` → `"mypart-rev1"`, `"pn"` → `"mypart"`, `"rev"` → `"rev1"`, `"R"` → `"1"`. Used by fileio for special paths (e.g. revision history) and inside `file_structure()` for dynamic filenames.
- **`state.file_structure`** — The default structure dict used by `fileio.path()` and `fileio.dirpath()` when you don’t pass `structure_dict`. The CLI sets this by calling **`state.set_file_structure(product_module.file_structure())`** after verifying the revision and loading the product.

So when you run a product: `verify_revision_structure()` ensures you’re in a revision folder and sets `state.pn` and `state.rev`; the CLI then sets `state.file_structure` from that product’s `file_structure()`. Product `file_structure()` functions typically use `state.partnumber("pn-rev")` (or similar) so filenames match the current part and revision.

## Resolving paths

- **`fileio.path("file key")`** — Returns the full path to the file whose structure entry has that **value** (the file key). Resolves relative to the current revision directory. Use this for files defined in your product’s file structure.
- **`fileio.dirpath("dirname")`** — Returns the full path to the directory whose **key** in the structure is that name. Resolves relative to the current revision directory.

To use a different structure (e.g. a macro with its own layout), pass it in:

- **`fileio.path("file key", structure_dict=my_structure)`**
- **`fileio.dirpath("dirname", structure_dict=my_structure)`**

Optional **`base_directory`** can be passed to both; it is joined after the revision directory.

## Special paths (no structure)

Some names are handled directly by fileio and do not come from the file structure:

- **`"revision history"`** — Part-level revision history TSV (e.g. `{partnumber}-revision_history.tsv` in the part directory).
- **`"library locations"`** — `library_locations.csv` at the Harnice repo root (created if missing).
- **`"project locations"`** — `project_locations.csv` at the Harnice repo root (created if missing).
- **`"drawnby"`** — `drawnby.json` at the Harnice repo root (created if missing).

## Other fileio functions

- **`fileio.part_directory()`** — Parent of the current working directory (the part folder).
- **`fileio.rev_directory()`** — Current working directory (the revision folder).
- **`fileio.read_tsv(filepath, delimiter="\t")`** — Reads a TSV into a list of dicts. `filepath` can be a filesystem path or a **file key**; if the path does not exist, fileio treats it as a key and resolves it with `fileio.path(filepath)`.
- **`fileio.get_path_to_project(traceable_key)`** — Looks up a project’s local path from `project_locations.csv` (at `fileio.path("project locations")`) and returns the expanded path for the given traceable key.
- **`fileio.silentremove(filepath)`** — Removes a file or directory and its contents if it exists.
