# Deleting a project leaves its folder behind

## Why
On 19 Oct 2026, `kanbanr project delete shop` removed `projects/shop/`, then wrote its own activity
entry ("delete project shop") into `projects/shop/activity/<day>.yaml`, which recreated the folder,
and committed it. The board then held a project folder for a project that no longer exists, and it
took a second, hand-made commit to remove it.

## Design

### Cause
The CLI backend appends every write to the project's activity day-log after the route runs
(`backend.rs`, `activity::append` → `daylog::append`), and `daylog::append` creates the directories
it needs. For a delete, the directory it creates is the one just removed.

### Fix
- `api/crates/kanbanr-core/src/daylog.rs`: `append` writes nothing when the project's folder does not
  exist. A log never brings back a project; the record of the delete is the board commit itself,
  whose message is "delete project <id>".
- The same guard covers the event log if it writes per project (checked in the test below).

### Test plan
| Req | Test | Where |
|---|---|---|
| R-1 | `project_delete_leaves_no_folder` (init a project, delete it through the CLI; `projects/<id>` does not exist and `git status` on the board is clean) | cli local_mode.rs |
| R-1 | `daylog::tests::append_never_recreates_a_project` | core daylog.rs |

### Implementation tasks
1. `daylog::append`: return early when `projects/<id>` is missing; unit test. Depends on: none.
2. CLI test `project_delete_leaves_no_folder`. Depends on 1.
3. CHANGELOG "Fixed" line with the docs sync. Depends on 2.

### Affects docs
None (behaviour fix; CHANGELOG only).
