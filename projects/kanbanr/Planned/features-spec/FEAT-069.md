# Agreement has to be revocable

## Problem
There is no way to withdraw an approval. `kanbanr approve` records agreement; nothing un-records it. A reviewer who changes their mind, or an approval recorded in error — by the wrong person, or by an agent that should not have recorded one at all — has no remedy short of editing the yaml by hand.

This was found the direct way: Claude approved FEAT-068 on the user's behalf, which the skill forbids, and there was no command to undo it.

## Behavior
- `kanbanr unapprove <CODE> --reason "…"` removes the current approval and records who withdrew it and why, so the withdrawal is as visible as the agreement was.
- The item returns to the review queue and the start gate applies to it again.
- The history of approvals and withdrawals stays on the item: agreement given and then taken back is more informative than no record at all, and the charter constraint says raw data is never discarded.
- `kanbanr approve --by` already records who agreed; a withdrawal records the same.

## Out of scope
A full audit trail of every approval event as a separate log — the item's own record is enough at this scale.