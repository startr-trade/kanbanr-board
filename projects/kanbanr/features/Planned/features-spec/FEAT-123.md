## Problem

Sprints and releases would exist only as text; the monitor would not show where an iteration stands.

## Behavior

Board sprint selector (active by default) and header (goal, dates, days left, committed vs done, burndown); a Releases page (scope, % done, target, notes); Gantt/Schedule show sprints as sections and releases as milestones.

See the design doc `design/process-as-configuration.md`.

## Opt-in per project

Sprints, releases and burn-rate reports (burndown, velocity) are **not for every project**: many follow a different workflow. They are switched on per project in the config (`cadence: {sprints: true, releases: true}`); the `scrum` and `agile` presets switch them on, every other preset leaves them off. With a capability off, its data file is never created, its monitor views and report sections are hidden, and its commands refuse with the one line that turns it on.

## Out of scope

- Editing sprints in the monitor.