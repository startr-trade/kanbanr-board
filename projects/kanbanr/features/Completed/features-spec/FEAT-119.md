## Problem

There is no timebox: milestones are themes with dependencies and carry no dates, so Scrum-style iterations cannot be planned or reviewed.

## Behavior

`projects/<id>/sprints.yaml` (SP-001: name, goal, start, end, capacity, state, carried); `sprint` on an item; `kanbanr sprint add|plan|start|close|show`; an `in_sprint` check; burndown and velocity derived from move history; `retro --sprint`.

See the design doc `design/process-as-configuration.md`.

## Opt-in per project

Sprints, releases and burn-rate reports (burndown, velocity) are **not for every project**: many follow a different workflow. They are switched on per project in the config (`cadence: {sprints: true, releases: true}`); the `scrum` and `agile` presets switch them on, every other preset leaves them off. With a capability off, its data file is never created, its monitor views and report sections are hidden, and its commands refuse with the one line that turns it on.

## Out of scope

- Per-person velocity or capacity (MS-005).