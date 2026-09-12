# GitHub issue mirror (kanbanr → GitHub via `gh`)

## Problem
Teams and collaborators often look at GitHub issues, not the kanbanr board. With `gh` installed, kanbanr can keep issues in step with the board. Two-way sync would create conflicts, so kanbanr stays the source of truth and GitHub is a mirror.

## Behavior
- **Opt-in per project:** `kanbanr mirror enable --repo owner/repo` writes `mirror.yaml` in the project (repo + `enabled_at`). It checks `gh` is installed and logged in, and **refuses a public repo unless `--allow-public`**, because specs and notes become public. The skill asks the user before enabling. `kanbanr mirror disable` turns it off (links are kept).
- **What gets mirrored:** a feature with an issue link is kept in step. A feature without one gets a new issue if it was created after `enabled_at` (or with `mirror sync --all`). Features in no-op states never get new issues.
  - Title = feature title. Body = a "tracked in kanbanr as `project:FEAT-012`" header, the spec, todo-lists as checklists, and a footer saying edits on GitHub are overwritten.
  - State: terminal status → closed (Completed → `completed`, no-op → `not planned`); otherwise open (reopened if needed).
  - Labels: the feature's labels; missing labels are created on the repo.
- **Change detection:** the rendered issue (title/body/state/labels) is hashed with a stable hash; the hash from the last push is stored on the link, so only changed features call `gh`.
- **Auto-sync after writes:** when enabled, every successful kanbanr write reconciles the project's features (best-effort: failures print a warning and never fail the write). New links/hashes are written back in a follow-up commit. `KANBANR_MIRROR=off` disables auto-sync for a session.
- **Commands:** `kanbanr mirror status` (config, `gh` availability, planned actions, no network writes); `kanbanr mirror sync [--all]`; `kanbanr mirror link FEAT-012 45` (link an existing issue); `kanbanr mirror pull FEAT-012` (read-only: remote state, whether the issue was edited on GitHub since the last push, comments since then) so Claude can bring changes back deliberately.
- **Import integration:** `feature.add` accepts an `issue` link, so features imported from GitHub (FEAT-042) mirror to the same issues instead of creating duplicates.
- **Monitor:** the feature page links to its issue.

## Out of scope
Inbound automatic sync; GitHub Projects boards; assignee/milestone mapping; GitLab (the tracker is behind a trait so it can be added later).
