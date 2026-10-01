## Problem

kanbanr is meant to show that it runs its own development: every item on its board says why it exists and how it is verified, every commit names the item it serves, and the reasoning, decisions, retros and lessons sit beside the work. None of that is visible to anyone else, because the board is a private folder on one machine. It cannot be published as it is: its eleven session summaries and a handful of documents carry private names and local paths, in the files and throughout 1,160 commits of history. And nothing in the code repository tells a reader where the board is or how to look at it.

## Behavior

**Sanitise, then publish `startr-trade/kanbanr-board`**
- A backup bundle first, outside any repository.
- The existing session summaries move to `.sessions/kanbanr/` (FEAT-135), and `projects/*/docs/sessions/` is removed from every commit of the history.
- The private terms (other projects' names, local paths) are replaced throughout the remaining files and the whole history, and a sweep of every blob and message shows none left.
- `kanbanr doctor` is clean afterwards and the monitor serves the board unchanged apart from the removed documents.
- The GitHub settings are listed for the maintainer: public; Actions, Issues, Wiki, Projects and Discussions off; secret scanning and push protection on; a `main` ruleset blocking force pushes and deletion with `kanbanr-maintainers` bypassing; no CI.

**Point the code repository at it — "kanbanr is developed with kanbanr"**
- README: a section showing the project managed with itself — the public board, the charter and its goals, an item with its definition and green tests, the ADRs, the retros and lessons, commits carrying `Refs: kanbanr:FEAT-…`, and `kanbanr why <file>:<line>` tracing a line to its requirement — with how to view the board live (clone it beside the code, `kanbanr serve`).
- A committed `.kanbanr` that points at `../kanbanr-board`, the documented layout, so a fresh clone beside the board just works.
- The contributing chapter: how to find the item behind a change, and how a pull request's definition relates to the board.
- The `CLAUDE.md` block names the board's URL, so a contributor's Claude can find it.
- The screenshots of kanbanr's own board stay real (FEAT-133): they are part of the evidence.

## Out of scope

- Pushing either repository: the maintainer does that.
