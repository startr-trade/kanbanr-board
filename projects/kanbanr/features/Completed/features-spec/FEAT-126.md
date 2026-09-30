## Problem

The code repository's 185 commits are authored with a work email, and a few tracked details are local: the `.kanbanr` marker naming the board folder, a home-directory path in a test, a stray previous owner in the plugin manifest, and four comments naming a sibling project. Publishing this history would make the email permanent.

## Behavior

- Fix the tracked details in this repository first: untrack and ignore `.kanbanr`, make the test path generic, point the plugin at `startr-trade/kanbanr`, and drop the sibling project's name from the comments (keeping their reasoning).
- Export the tracked tree to a new sibling folder, `kanbanr-public`, and start it as a new repository on `main` with one commit by `Venkatraman B <vb@startr.trade>`.
- Move the working setup there: its own `.kanbanr` marker (untracked) pointing at the same board, git hooks, the project's Claude Code hooks, the skill link and the installed binary.
- This folder stays as the private archive of the full history, never pushed.
- Verify: builds and tests pass in the new folder, its history is one commit by the new identity, and a sweep finds no private identifiers.

## Out of scope

- Creating the GitHub repository, pushing, and making it public (the user's steps).