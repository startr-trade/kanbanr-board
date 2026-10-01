## Problem

Session summaries (FEAT-099, FEAT-101) are written as board documents, `docs/sessions/<date>-<time>-<sid>.md`, through `kanbanr doc add`, so each is committed to the board's history and pushed with it. A summary is a condensed conversation: it names local paths, other projects and half-formed ideas, and the exclusion list only removes the terms someone thought to list. On kanbanr's own board every one of the eleven summaries carries text that must not be public, and a board is exactly what a team shares through a remote.

## Behavior

- The summariser writes each summary to `<board>/.sessions/<project>/<date>-<time>-<sid>.md`, a plain file beside the board it summarises: never committed, never pushed, not shown among the project's docs. The exclusion list is still applied on the way out.
- Every board ignores `.sessions/`: it is added to the data repository's `.gitignore` the same way the secrets file and lock are, on the next write, for existing boards too.
- Recovery is unchanged: a session recovers from the board, not from summaries; summaries are a record to consult.
- The skill, the hooks README and the docs say where summaries live and that they are local.

## Out of scope

- Moving and purging kanbanr's own existing summaries from the board's history (FEAT-136).
