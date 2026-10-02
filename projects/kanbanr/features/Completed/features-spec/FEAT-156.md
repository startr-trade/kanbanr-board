# Defect: finishing an item's last task completes it with its requirements unproven

## Problem
On a workflow with no declared gates (the default, and this board), ticking an item's last task
auto-advances it to the end status even when its requirements have no green test. `kanbanr finish`
refuses the same move ("requirements unproven"), so the two ways an item finishes disagree — and
auto-completion is how most items finish (FEAT-061).

It happened on this board: a batch that recorded one completed task and then added two open proof
tasks moved FEAT-149 and FEAT-152 to Completed between its operations, with requirements still
planned. Both were moved back by hand. A scratch board reproduces it with one `task state`.

## Behavior
- Auto-advance into an end status requires what `finish` requires: every requirement of a defined
  item proven by a green test. When it does not hold, the item stays where it is and the task
  write says why (as gated workflows already do).
- Items with no definition, and items created before the charter was adopted, keep today's
  behaviour.
- A batch is judged when it ends, not between its operations: an item whose last task completes
  inside a batch that then adds open tasks to it does not advance.

## Out of scope
Changing what a declared gate requires.
