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

Mode is determined by the selected item in Project files (`selectedFile`). Toolbar and content are updated from a single place when the selection changes.

## Data flow

1. **EditorShell** (or equivalent) holds: `selectedFile`, `editorFiles`, `productType`. It is the single source of truth for “what is shown.”
2. **Toolbar** is rendered from a spec keyed by mode (e.g. `TOOLBAR_SPEC[selectedFile]`). Feature-tree mode uses native controls (save, dropdowns); network modes use buttons that either call into the graph API (postMessage to iframe) or, in a future in-process refactor, call a graph module directly.
3. **Content** switches between the feature-tree editor (textarea + output) and the graph editor. The graph editor currently runs in an iframe and receives actions via postMessage; the parent never duplicates toolbar buttons inside the iframe (they live only in the shell toolbar).

## Files

- **feature_tree_editor.html** — Single entry point. Markup is the shell (left panel, right area, one toolbar, one content). Script drives toolbar and content from view state.
- **feature_tree_server.py** — Serves the editor, /api/* for code and run, and /api/available, /api/chosen_list, etc. for the graph editor. No separate graph editor server in process.
- **graph_editor.html** — Loaded in the content area (iframe) when the view is a network file. When embedded it hides its own tabs and main toolbar; the shell toolbar is the only one. It handles postMessage for setTool and fitView.

## Future: graph in process

To remove the iframe, the graph editor would be initialized into a mount node (e.g. `#graph-editor-root`) in the same document: load graph HTML fragment + graph JS, then call `HarniceGraphEditor.init(mount)`. The shell toolbar would call `HarniceGraphEditor.setTool()` / `fitView()` / `switchTab()` directly. That requires extracting the graph editor script to a root-scoped or mount-scoped module (e.g. `document.getElementById('graph-main')` with the fragment using `id="graph-main"`).
