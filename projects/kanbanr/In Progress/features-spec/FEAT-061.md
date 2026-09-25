# Defect: the most common way an item finishes records no transition

## Problem
`kanbanr retro MS-006` reported "no recorded moves, so no flow numbers" for nine items that had demonstrably been worked on and completed — including items completed after transition history shipped.

## Root cause
Ticking the last task auto-completes the item by assigning `f.status` directly in `set_task_state_on`. Only `move_feature_on` appends to `history[]`. Since auto-completion is how most items actually reach a terminal status, the cycle-time and time-in-status numbers are missing for exactly the items that finished normally, and present only for those moved by hand.

## Behavior
- An auto-completion records the same transition a manual move does.
- A status *rename* still records nothing: the item did not move, the status was relabelled.

## Out of scope
Backfilling the items that already finished without a transition — the activity-log fallback covers what it can, and inventing the rest would be worse than the gap.