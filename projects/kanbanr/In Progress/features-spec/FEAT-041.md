# Data folder next to the project (`<project>.kanbanr`), chosen at activation

## Problem
The data folder resolves from `--data-dir` → `$KANBANR_DATA_DIR` → `./data` **relative to the current directory**. So by default the board is a git repo nested inside the project's own git repo (it has to be gitignored, is easy to commit by accident, clutters search and watchers), and running `kanbanr` from a subfolder doesn't find the board. The `.kanbanr` marker stores only the project name, not where the data lives.

## Behavior
- **Chosen at activation.** `kanbanr init` asks where to keep the board. The default is a sibling of the project's **git repo root** (not the cwd), named `<repo>.kanbanr` (e.g. `~/code/app` → `~/code/app.kanbanr`). Existing `*.kanbanr` folders next to it are offered too, so several projects can share one data folder (portfolio, cross-project Gantt, cross-project deps only work within one data folder). Or type any path.
  - Interactive terminal: a prompt. Non-interactive (Claude via Bash): uses `--data-dir` if given, else the default, and prints where. The **skill** makes Claude ask the user (with the options from `kanbanr where --json`) before running `init`.
  - Warns if the chosen folder is inside another git work tree.
- **Recorded in the marker.** `.kanbanr` becomes YAML: `project: app` + `data_dir: ../app.kanbanr` (relative to the marker's folder). A legacy one-line marker (just the name) still works; when there's no data_dir to record the legacy form is written.
- **Found from anywhere.** The CLI walks up from the cwd to the nearest `.kanbanr` marker. Data dir order: `--data-dir` → `$KANBANR_DATA_DIR` → marker `data_dir` → `./data` (legacy). `serve` and hooks use the same resolution.
- **`kanbanr where`** prints the resolved data folder; `--json` adds source, marker, project, suggested default, existing nearby kanbanr folders, and whether a path is inside a git repo.
- `kanbanr project use <name>` keeps the marker's data_dir (or records `--data-dir` if passed).

## Out of scope
Moving existing `./data` boards (they keep working unchanged).
