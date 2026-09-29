## Problem

The first real run of the FEAT-100 interview (katalog, 2026-09-29) worked end to end, but showed four gaps in the skill text:

1. The skill described goals as "an outcome plus a measure", so Claude wrote `outcome:` and the first `charter set` failed; the field is `statement`. The skill never gives the charter's exact shape.
2. The user listed three items under non-goals that were really goals; Claude caught it only after the first ExitPlanMode. The skill should say to check each non-goal reads as something the project will *not* do.
3. The folder was not a git repo. Claude ran `git init` (fine, it was in the plan), but nothing covered the first commit, which the hooks then refused (FEAT-105).
4. After setup, Claude could not find how to view the board and started this repository's dev build (FEAT-104). The skill should end setup by naming `kanbanr serve` / `kanbanr open`.

## Behavior

The Activation section gives the exact `charter.yaml` shape; tells Claude to sanity-check non-goals; when the folder is not a git repo, puts `git init` and an initial commit (the marker, CLAUDE.md, .gitignore) in the plan, before `git install-hooks`; and ends with how to view the monitor.

## Out of scope

- Changing the interview's flow, which worked.