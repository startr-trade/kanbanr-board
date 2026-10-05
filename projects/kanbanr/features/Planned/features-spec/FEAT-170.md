# Projects told when their saved process changes, updated on request

## Problem
Once a saved process changes, the projects that applied an earlier version keep the old gates and
nobody is told.

## Behavior
- `kanbanr process diff [--project P]`: what differs between the project's workflow and the saved
  version it came from (statuses, transitions, gates).
- `kanbanr process update [--project P]`: applies the saved current version; refused when a status
  that still holds items would disappear, naming `config rename-status`.
- `doctor` warns when the library has a newer version than the project's, and when the project's
  workflow was edited after it was applied.
- The SessionStart summary names an available update in one line.
- The monitor's Workflow page shows "Process: <name> v<n> (<library>)" and the drift notice.
- In-flight items meet new gates on their next move; approvals stay valid.

## Out of scope
Applying changes automatically; merging two diverged versions.
