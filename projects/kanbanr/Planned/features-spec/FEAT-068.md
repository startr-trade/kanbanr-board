# Defect: a warning that cannot be answered

## Problem
The user approved all twelve pending definitions — the first real use of the approval gate. Eleven of them still report `0/1 ready`, and `doctor` still warns, because `started_unapproved` keeps warning forever once it is set.

The warning's own text asks the reader to "review and approve what was actually built". They did. The warning did not notice.

## Root cause
`check_report` and `doctor::scan_definitions` raise the warning whenever `started_unapproved` is non-empty, with no reference to whether the definition has since been approved. The record and the warning were treated as the same thing.

## Behavior
- The **record** stays on the item: work did start before agreement, that is history, and the charter constraint says raw data is never discarded. It remains visible in `feature show` and in the review brief.
- The **warning** fires only while the approval is missing or lapsed. Once the definition is agreed, the escape has been reviewed — which is precisely what the warning asked for — so it stops.
- An item that is approved and then has its definition changed lapses the approval, and the warning returns with it, because the agreement no longer covers what was built.

## Out of scope
Removing the field, or clearing it on approval. A record that disappears when it becomes convenient is not a record.