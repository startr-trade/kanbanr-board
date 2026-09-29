## Problem

`kanbanr claude guard` refused a write to `~/.claude/plans/<plan>.md` — the file Claude Code's plan mode requires — because the session's project is tracked, and told Claude to run `kanbanr doc add notes/~/.claude/plans/…`, a path no one could use. A guard that blocks the harness's own files gets turned off.

## Behavior

The guard decides only for paths inside the tracked project's repository. A path outside it (absolute or `..`-escaping) passes silently. The suggested board path is built from the repo-relative path, never an absolute one.

## Out of scope

- Changing which in-repo files count as deliverables.