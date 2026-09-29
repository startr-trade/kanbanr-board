## Problem

`start` branches at the first active status (too early under TOGAF), `finish` jumps to the first terminal status even when no transition allows it, and auto-advance targets a status literally named "Completed" and skips every check.

## Behavior

`start` targets the status whose gate has `on_enter: [branch]` (branching only in a git repo); `finish` targets a terminal status reachable by an allowed transition and evaluates its gate; auto-advance targets an allowed terminal status and fires only when its gate passes; `first_active_status` excludes no-op statuses.

See the design doc `design/process-as-configuration.md`.

## Out of scope

- New statuses or presets.