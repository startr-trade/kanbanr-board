# events.yaml is always one write behind git

## Problem
Eventing (FEAT-036) appends to `projects/<id>/events.yaml` AFTER the commit, by design — it is a best-effort tail step that must never fail or delay a durable write. The consequence is that the event just written stays uncommitted in the data repo until some later write commits it, so `git status` in the board repo is dirty after the last operation of a session and the final events of a session are unversioned until the next one.

## Behavior
Decide between: (a) append the event BEFORE the commit so it is included (changes the durability ordering, and a webhook failure must still not fail the write); (b) commit the event log in a second, cheap commit after delivery; or (c) accept it and have `kanbanr doctor` note an uncommitted event log rather than leaving it silently dirty.

## Out of scope
Changing webhook delivery semantics.
