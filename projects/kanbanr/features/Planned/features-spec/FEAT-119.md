## Problem

There is no timebox: milestones are themes with dependencies and carry no dates, so Scrum-style iterations cannot be planned or reviewed.

## Behavior

`projects/<id>/sprints.yaml` (SP-001: name, goal, start, end, capacity, state, carried); `sprint` on an item; `kanbanr sprint add|plan|start|close|show`; an `in_sprint` check; burndown and velocity derived from move history; `retro --sprint`.

See the design doc `design/process-as-configuration.md`.

## Out of scope

- Per-person velocity or capacity (MS-005).