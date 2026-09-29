## Problem

When Claude sets a project up with kanbanr, the skill asks for the board folder, runs `init`, and leaves the charter, the workflow (default, TOGAF or custom) and the git hooks to be discovered later, piecemeal. Step 0 even asks for the charter before the board it is written to exists. The result is a project that starts work before its purpose and process were agreed — the setup-level version of the failure G-3 exists to prevent.

## Behavior

When the user asks Claude to set up / init kanbanr and the folder is not yet tracked, the skill enters **plan mode** before doing anything else and collects, in one plan:

1. **Board and identity** — data folder (suggested `<repo>.kanbanr`, an existing board, or a typed path), project name and description, commit author and email (defaulted from `git config`).
2. **Charter** — purpose, goals with measures, non-goals, stakeholders, constraints. Drafted from what the repo already says (README, manifests) and marked as a draft; anything the repo cannot answer is left blank and asked, never invented.
3. **Process** — workflow: default kanban, TOGAF phases, or custom statuses; Zachman six-column definitions are the method on every item regardless; enforcement choices: git commit-msg/pre-commit hooks, a git remote for backup, the GitHub issue mirror, and whether to import an existing tracker.

The plan lists the exact commands it will run. **Exiting plan mode is the approval**: Claude then runs the whole setup — `init`, workflow, `charter set`, Claude Code hooks, `git install-hooks`, `claude sync`, remote, import — saves the approved plan as a board doc, verifies with `hooks status`, `git status` and `doctor`, and only then returns to whatever the user originally asked for. A project already tracked skips all of it.

## Out of scope

- A new CLI command; the existing commands already cover every step.
- Running the interview when the user types `kanbanr init` in their own terminal (no Claude involved).