# Feature tree editor GUI layout

## Architecture

Single-window editor with one layout for all file types. No structural difference between editing the feature tree and editing network files—only the toolbar contents and the main content change.

## Structure

```
#app
├── #main (flex row)
│   ├── #left-panel (fixed width)
│   │   ├── #left-panel-header   [Render button, part number]  (always visible)
│   │   ├── #file-navigator     [Project files list]
│   │   └── #projects-section   [Projects list]
│   └── #right-area (flex column, fills rest)
│       ├── #top-toolbar        (one strip; contents depend on view mode)
│       └── #content-section   (one area; contents depend on view mode)
```

## View modes

- **feature tree** — Toolbar: save indicator, insert dropdowns. Content: textarea + output.
- **available network** — Toolbar: Select, Add Node, Add Segment, Delete, Fit View. Content: graph editor (available panel).
- **chosen network** — Toolbar: Fit View. Content: graph editor (chosen panel).
- **flattened network** — Toolbar: Fit View. Content: graph editor (flattened panel).
- **system list panes** (system product only) — Instances Lists, Devices, Circuits, Harnesses, Channel Map, Disconnect Map appear as project files. Selecting one shows the in-DOM system list view (table, filters, column dropdown, SSE, device/signals expand). Toolbar: search, clear filters, row count badge, sort dropdown; content: system list panel (no iframe).

Mode is determined by the selected item in Project files (`selectedFile`). Toolbar and content are updated from a single place when the selection changes.

## Data flow

1. **EditorShell** (or equivalent) holds: `selectedFile`, `editorFiles`, `productType`. It is the single source of truth for “what is shown.”
2. **Toolbar** is rendered from a spec keyed by mode (e.g. `TOOLBAR_SPEC[selectedFile]`). Feature-tree mode uses native controls (save, dropdowns); network modes use buttons that either call into the graph API (postMessage to iframe) or, in a future in-process refactor, call a graph module directly.
3. **Content** switches between the feature-tree editor (textarea + output) and the graph editor. The graph editor currently runs in an iframe and receives actions via postMessage; the parent never duplicates toolbar buttons inside the iframe (they live only in the shell toolbar).

## Files

- **feature_tree_editor.html** — Single entry point. Markup is the shell (left panel, right area, one toolbar, one content). Script drives toolbar and content from view state.
- **feature_tree_server.py** — Serves the editor, /api/* for code and run; /api/available, /api/chosen_list, etc. for the graph editor; /system-list-view.js and /api/files, /api/sse, etc. for system list panes (system product). Uses **system_viewer_core** for tab list and file watcher; uses **system_viewer_server** for system API handlers.
- **graph_editor.html** — Loaded in the content area (iframe) when the view is a network file. When embedded it hides its own tabs and main toolbar; the shell toolbar is the only one. It handles postMessage for setTool and fitView.
- **system_list_view.js** — In-DOM system list view: table, viewer headers (instances/channel/disconnect/circuits), column filter/sort dropdown, SSE, device row → signals list expand, channel-type display. Loaded by the feature tree editor; mounts inside #system-list-panel when a system list pane is selected. Exposes SystemListView.loadPane(), setSearch(), clearFilters(), setSort(), getState(), setOnStateChange().
- **system_viewer_core.py** — Shared data and logic for system lists: tab order/labels, get_all_files(), get_tab_list(), file watcher, SSE queues, signals-list content. Used by feature_tree_server and by system_viewer_server (standalone).
- **system_viewer_server.py** — Thin HTTP layer: serves system_viewer.html and system API (files, sse, channel-type, signals-list). Used by feature_tree_server for system API routes and by CLI/launcher for standalone system viewer.
- **system_viewer.html** — System list table/filters UI for **standalone** use only (full page with left tab bar). The feature tree editor uses **system_list_view.js** in-DOM instead of this iframe.

## Single server

Only the feature tree server is used for the GUI. The CLI flags `--gui`, `--graph-editor`, and `--system-viewer` all launch the same server (feature tree editor) with the current or given revision; graph and system list panes are view modes inside that editor. The standalone `graph_editor_server` and `system_viewer_server` modules are no longer invoked from CLI or launcher.

## Future: graph in process

To remove the iframe, the graph editor would be initialized into a mount node (e.g. `#graph-editor-root`) in the same document: load graph HTML fragment + graph JS, then call `HarniceGraphEditor.init(mount)`. The shell toolbar would call `HarniceGraphEditor.setTool()` / `fitView()` / `switchTab()` directly. That requires extracting the graph editor script to a root-scoped or mount-scoped module (e.g. `document.getElementById('graph-main')` with the fragment using `id="graph-main"`).
