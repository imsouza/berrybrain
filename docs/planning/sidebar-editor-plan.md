# Sidebar and Markdown Editor Plan

## Goal

Make BerryBrain's workspace feel like a serious vault-based second brain:

- organize notes by vault folders and subfolders;
- create, rename, and delete folders from the sidebar;
- keep the sidebar compact, readable, and professional;
- provide a full markdown writing workflow with edit, preview, split view, toolbar, and keyboard shortcuts;
- keep all application UI in English while preserving user note content exactly as written.

## Current Decision

Folders are managed from the filesystem, not from a new `FolderRecord` table.

Reason: the vault directory is already the source of truth. Adding a folder table without full bidirectional sync would create a second source of truth and likely introduce folder duplication or stale records. If folder metadata is needed later, it should be added only after a sync contract is defined.

## Phase 1: Folder API

Status: applied.

Implemented endpoint surface:

- `GET /api/v1/folders`
- `POST /api/v1/folders`
- `PUT /api/v1/folders/{folder_path:path}`
- `DELETE /api/v1/folders/{folder_path:path}`

Behavior:

- lists folders recursively;
- returns `name`, `path`, `parent_path`, `depth`, `note_count`, `total_note_count`, and `has_subfolders`;
- creates root folders or subfolders through `parent_path`;
- renames folders by relative path;
- deletes only empty folders;
- blocks absolute paths and `..` traversal.

Deferred:

- moving notes between folders;
- deleting non-empty folders by moving notes elsewhere;
- persistent folder metadata.

## Phase 2: Sidebar Folder Tree

Status: applied.

Implemented:

- folder grouping in the vault sidebar;
- recursive folder display with indentation;
- collapse/expand per folder;
- create root folder;
- create subfolder from an existing folder row;
- rename folder;
- delete empty folder;
- direct note count and total note count metadata;
- notification bell next to settings;
- English-only sidebar labels.

Deferred:

- drag and drop note moves;
- context menu;
- folder icons;
- multi-select operations.

## Phase 3: Markdown Editor

Status: applied as a lightweight implementation.

Implemented:

- edit, preview, and split modes;
- markdown toolbar;
- bold, italic, heading, quote, unordered list, ordered list, link, image, inline code, code block, table, and horizontal rule insertion;
- keyboard shortcuts:
  - `Ctrl/Cmd+B` for bold;
  - `Ctrl/Cmd+I` for italic;
  - `Ctrl/Cmd+K` for link;
  - `Ctrl/Cmd+Shift+C` for code block;
  - `Ctrl/Cmd+Shift+L` for list;
- GFM preview through the existing markdown preview pipeline.

Deferred:

- full syntax highlighting dependency;
- slash command menu;
- markdown linting;
- table editor controls.

## Phase 4: English-Only UI

Status: applied.

Implemented:

- the i18n layer now resolves the application language to English;
- the settings language selector is replaced by a note that user notes keep their original language;
- API labels, Home summary labels, graph inference messages, notification labels, worker-generated note templates, and main UI actions were translated to English;
- compatibility checks for old Portuguese draft names and legacy hidden insight titles remain internal only.

## Acceptance Checklist

- The sidebar can show vault folders and subfolders.
- A user can create a root folder.
- A user can create a subfolder.
- A user can rename a folder.
- A user can delete an empty folder.
- Folder paths are protected from traversal.
- Notes remain grouped by their real vault path.
- The editor has a visible markdown toolbar.
- The editor has real-time preview and split view.
- Main keyboard shortcuts work.
- The application UI is English-only.
- User note content is not translated.

## Next Improvements

- Add drag and drop to move notes between folders.
- Add `POST /api/v1/notes/{path}/move` for safe note movement.
- Add optional folder metadata after defining a sync contract.
- Add `react-syntax-highlighter` or Prism if full code highlighting becomes necessary.
- Add focused tests for folder CRUD and editor formatting behavior.
