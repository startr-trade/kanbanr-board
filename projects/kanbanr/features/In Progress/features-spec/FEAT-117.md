## Problem

Nothing tells Claude or the user what the next stage needs, so definitions are either filled all at once or not at all, and doctor warns about every possible gap.

## Behavior

`check` prints what the next status or statuses require; doctor warns only about the next gate (plus `warns:`); the review queue lists items blocked for want of approval or a sign-off, with Approve/Ratify/Sign off buttons; the monitor's Workflow page shows each status's purpose, checks, sign-offs and enforcement, and board cards carry a next-gate chip; `claude sync` writes each status's purpose into CLAUDE.md.

See the design doc `design/process-as-configuration.md`.

## Out of scope

- Editing workflows in the monitor.