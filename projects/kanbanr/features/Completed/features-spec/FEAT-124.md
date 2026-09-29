## Problem

The session-summary hooks write a summary of every session to the board. Some things discussed in a session are confidential to the user and must never reach the board — not in the summary, not in its git history. Nothing lets the user say so, and the summariser sends the whole transcript to the model.

## Behavior

- A private exclusion list lives outside the repository and the board (default `~/.claude/kanbanr-summary-exclude.txt`, or `$KANBANR_SUMMARY_EXCLUDE`), one term per line, matched case-insensitively.
- Before summarising, every transcript message containing a listed term is dropped, so the model never sees it.
- After summarising (and for a compaction's own summary, which is saved verbatim today), every line containing a listed term is removed before anything is written.
- The repository and the board never contain the list's contents; the code only names the file.

## Out of scope

- Rewriting summaries already on the board.