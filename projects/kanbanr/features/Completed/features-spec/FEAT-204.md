# A sign-off that clears the last hold finishes the item

## Why
On 20 Oct 2026 FEAT-191 and FEAT-201 had every task done and were held at In Progress by their
end gate's `docs-folded` sign-off. The user gave it in the monitor; neither moved, and the board
showed finished work as in progress until someone moved them by hand. Auto-completion
([FEAT-061](/p/kanbanr/feature/FEAT-061), [FEAT-156](/p/kanbanr/feature/FEAT-156)) runs only when
the last task is ticked; nothing re-checks when the hold is lifted by a sign-off.

## Design
- `api/crates/kanbanr-core/src/store.rs`: the auto-completion block that runs after a task write
  becomes `fn auto_complete(project, charter, ctx, code) -> (Option<String> /*moved to*/, Option<String> /*held*/)`,
  called by the task write (as now) and by `signoff_feature` after the sign-off is recorded. Same
  rules: every task done, not in a no-op status, the end status's gate passes, FEAT-156's evidence
  rule, and FEAT-190's hold when completing would merge a branch.
- The sign-off's response (route and CLI) says what happened: "FEAT-191 -> Completed", or why it
  stays ("still held: …").
- A withdrawn sign-off never moves anything.

### Test plan
| Req | Test | Where |
|---|---|---|
| R-1 | `signoff_completes_a_held_item` (core: an item with all tasks done held for `docs-folded`; the sign-off moves it to the end status with a history entry; an item with an open task, or still held by another sign-off, stays) | core lib.rs |

### Implementation tasks
1. Extract `auto_complete`; call it from the sign-off; the response text (route and CLI); R-1.
2. CHANGELOG "Fixed"; make ci.

### Affects docs
None (behaviour fix; CHANGELOG only).
