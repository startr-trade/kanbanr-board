# SCM traceability: branch per item, commit trailers, git hooks

## Problem
Nothing ties a code change to the item that justifies it, and nothing stops work landing on the default branch without a reference.

## Behavior
- Commit trailer `Refs: kanbanr:FEAT-046/R-2` (requirement level; `/TL-001/T3` for a task); `kanbanr commit -m` fills it from the active item.
- `kanbanr git install-hooks` (core.hooksPath, never clobbering existing hooks): `commit-msg` rejects a missing or unknown reference, `pre-commit` refuses the default branch; merges, reverts and a recorded `[no-ref]` escape are allowed.
- A Claude Code PreToolUse hook on `git commit` gives the same feedback before the attempt.
- `kanbanr start <CODE>` branches `feat/{code}-{slug}`; the branch is the active-item signal, removing ambiguity for the trailer and the test-capture hook. A commit may reference several items; `spike/*` cannot be merged; renaming a code renames the branch or fails.
- The board's own data repo is exempt.

## Out of scope
Hosting-specific PR automation.
