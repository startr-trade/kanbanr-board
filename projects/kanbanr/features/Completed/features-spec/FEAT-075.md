# Defect: deferring an item is not starting work on it

## Problem
The start gate treats any status that is not the default, not terminal and not a no-op disposition as "starting work". `Deferred` is none of those three, so moving an item to `Deferred` is refused for want of an approval — even though parking an item is the opposite of beginning it.

Found while deferring FEAT-074: the item was deliberately not being built, and the gate demanded its reasoning be agreed first. The only ways past were to approve something nobody intended to start, or to record an `--unapproved` escape for a non-event. Both teach that the escape is routine, which is the failure the gate exists to prevent.

## Root cause
The gate infers "active" by elimination rather than from anything the workflow states. `displayed_states` already carries the needed meaning — the statuses shown on the kanban, where work in flight lives — and a parking state is deliberately not among them.

## Behavior
- The gate applies to a status that is **displayed**, not the default, not terminal and not a no-op. On this board that is exactly `In Progress`; on the default workflow, exactly `Scheduled`.
- Parking an item in a non-displayed state such as `Deferred` is never gated.
- Everything else about the gate is unchanged, including the recorded `--unapproved` escape for the case it is meant for: beginning work anyway.

## Out of scope
Adding a separate list of active states to the config. `displayed_states` already means this, and a second list would be one more thing to keep in step.