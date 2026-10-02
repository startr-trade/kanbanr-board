# Accept or reject an architecture decision from the CLI and the Review page

## Problem
`kanbanr adr new` drafts a decision as `proposed`, and the method says a decision is the user's to
make — but nothing lets the user make it. The CLI has `new`, `list`, `supersede` and `history`; the
Review page lists definitions to approve and sign-offs, not decisions. Accepting ADR-0012 meant
editing its front-matter by hand. A proposed decision therefore sits unanswered, or Claude edits
the status itself, which the method forbids.

## Behavior
- `kanbanr adr accept <ADR-ID>` and `kanbanr adr reject <ADR-ID> --reason "…"` record the verdict:
  the status, the decider (the commit identity), the date, and for a rejection the reason, in the
  decision's front-matter; one commit each.
- Accepting a decision with an unanswered section (Context, Decision, …) is refused, naming the
  sections.
- The Review page lists proposed decisions beside the definitions waiting for approval, with
  Accept and Reject buttons (Reject asks for a reason), available where the monitor's verdict
  buttons already are (`serve --allow-writes`).
- The skill says a decision is accepted by the user, never by Claude, as for approvals.

## Out of scope
Editing a decision's text in the monitor; voting or multiple deciders.
