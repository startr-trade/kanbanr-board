# Import existing task trackers into kanbanr

## Problem
Projects that adopt kanbanr often already track work somewhere: `TODO.md`/`ROADMAP.md` checklists, planning files from other AI dev tools (Spec Kit `tasks.md`, Kiro `.kiro/specs/*/tasks.md`), GitHub/GitLab issues, or Jira/Linear exports. Starting from an empty board loses that work, and leaving the old tracker live creates two conflicting plans.

## Behavior
- **Offered at activation** (skill): after the board folder is chosen, Claude looks for existing trackers, lists what it found, and asks which to import. Default: open + in-progress items only; finished items only on request (as Completed). `TODO:`/`FIXME` code comments only on request.
- **Mapping** (skill): epics/milestones → milestones; issues/stories → feature items (description → spec); sub-checklists → tasks; statuses → the project workflow (unclear ones flagged, not guessed); labels, priority, due, "blocked by" → fields/dependencies.
- **Preview, then one commit:** `kanbanr batch --dry-run` validates the bundle and reports what would be created or skipped, writing nothing. The real `kanbanr batch` is one git commit in the board repo.
- **Provenance, not a live pointer:** `feature.add` accepts `source` = `{system, ref, revision, url}`. kanbanr stamps `imported_at` and a stable `key`. The source is history: nothing depends on it still existing.
  - `original` (the item's original text) is appended to the spec as an "Imported from" section, so the content survives if the source is deleted or its git history rewritten.
  - For file sources, the CLI fills `revision` with the project repo's HEAD commit.
  - Whole files being retired are copied into kanbanr docs under `imports/` first (skill, via `doc.write`).
- **Re-import is safe:** the `key` is `<system>:<ref>` for issue trackers (stable identity) and a hash of the normalized title for files (location-independent, so moved/renumbered/deleted files don't re-import). A `feature.add` whose key already exists is skipped, and the ops in the bundle that target it (todo/task ops) are skipped too.
- **Missing sources are labeled honestly:** `kanbanr sources` (run in the project folder) lists sources and checks whether file sources still exist; `--write` records `missing_since` (cleared if the file comes back). The monitor shows "source no longer present" instead of a broken link.
- **Retiring the old tracker** (skill, always asks): leave it; replace a file with a pointer to kanbanr; for GitHub issues, comment and/or close via `gh`.

## Out of scope
Two-way sync (see FEAT-043 for the kanbanr → GitHub mirror). Dedicated per-format importers.
