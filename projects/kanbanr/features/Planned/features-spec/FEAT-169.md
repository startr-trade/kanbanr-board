# Saved processes: on the board or personal, reused by name

## Problem
A process lives only in the project it was applied to. Another project, or a teammate, copies the
YAML by hand.

## Behavior
- Three libraries, looked up in this order: the board (`<board>/processes/<name>.yaml`, shared through
  the board's remote), personal (`~/.kanbanr/processes/`, `KANBANR_PROCESSES_DIR` overrides), built-in.
  A saved process may not take a built-in name; a board copy shadows a personal one and `list` says so.
- A process file gains an optional `process: {name, description, version}` header; older binaries
  ignore it.
- `kanbanr process list | show <name> | save <name> [--from-file F | --from-project P] [--personal]
  [--description D]`. Save bumps the version only when the content changed; a board save is one
  commit. The user chooses board or personal on every save; the CLI defaults to the board.
- `config workflow --preset <name>` and `project init --workflow <name>` resolve saved processes.
- Applying a named process records `process: {name, library, version, rev}` on the project's config
  (kept by older binaries through `extra`, so no schema bump); `--from-file` or field flags clear it.
- Routes: `GET /processes`, `GET /processes/{name}`, `PUT /processes/{name}`.

## Out of scope
Drift and updates (the next item); a registry outside the board.
