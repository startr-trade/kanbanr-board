# Reviewing a definition is reading, and reading belongs in the reader

## Problem
A definition brief is a page of markdown: a statement, six dimensions in a table, requirements with their test evidence. Reading eleven of those in a terminal, then typing an approve command for each, is the wrong medium for the job — and the approval gate's own premise is that agreement must be cheap or it becomes theatre. The gate has been escaped on every item so far, and friction is part of why.

The daemon already has a sanctioned write mode (`serve --allow-writes`, FEAT-034); what is missing is the affordance. Saying the UI cannot approve was wrong: it can, it just has no button.

## Behavior
- The daemon reports whether it accepts writes, so the UI can offer the action only when it is real rather than failing on click.
- A **Review** surface lists every item whose definition is not currently agreed — never approved, or lapsed because the definition changed after a yes — rendered as the brief a reader wants: statement, goals, the six dimensions, requirements with their evidence.
- Approving from that surface records the same approval the CLI does, through the same route, pinned to the same content hash. There is no second code path and no second notion of what agreement means.
- `kanbanr review --ui` starts the daemon with writes enabled and opens the browser on that surface, so one command replaces reading eleven briefs in a terminal.
- Read-only stays the default. Nothing about the ordinary monitor changes, and a daemon started without writes shows the queue but offers no button.

## Out of scope
Editing a definition in the browser — a definition is authored as YAML and reviewed as rendered text; making it editable in two places is how the two copies disagree. Rejecting with a comment, which needs somewhere to put the comment.