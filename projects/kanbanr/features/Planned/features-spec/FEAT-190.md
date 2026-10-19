# Stage-driven merges and carry-over

Scope:
- **Integrate.** When an item enters the status with the `integrate` role and its gate is met (tests green), kanbanr merges its branch into the line of integration with `--no-ff` and the item's `Refs`. It refuses on conflict and leaves everything as it was.
- **Release terminal.** When a release is cut (FEAT-183), or a sprint closes in the sprints-only model, the line is fast-forwarded into main and tagged. If that is not a fast-forward, it stops.
- **Carry-over.** `sprint close --carry-to` keeps unfinished item branches open. When the next sprint branch exists, kanbanr merges it *into* each carried item branch (catch-up, never a rebase). Conflicts are reported for the item.
- **Fixes move forward.** Fixes on a release branch, and patch releases, are merged forward into the current line of integration.
