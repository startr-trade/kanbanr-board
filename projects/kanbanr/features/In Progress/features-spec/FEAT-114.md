## Problem

Some stage conditions are not visible in board data — a design review held, a release approved. Without a record they are either skipped or kept elsewhere.

## Behavior

`signoffs: [{id, by, at, note, doc, rev}]` on an item, appended, never overwritten. `kanbanr signoff <CODE> <id>` and a route (and a Review-page button, in the surfacing item) record one as the commit identity. It pins `content_rev`, so a later definition change lapses it. Gates require them as `signoff:<id>`. Approval events gain the status they were given in.

See the design doc `design/process-as-configuration.md`.

## Out of scope

- Multi-approver quorum or roles.