## Problem

Estimates exist only in days, and nothing records a project's sprint length or release cadence.

## Behavior

`points` on an item beside `estimate_days`; `estimate_unit: points|days` and `cadence: {sprint_length_days, release}` in the config; an `estimated` check using the project's unit; capacity and velocity in that unit.

See the design doc `design/process-as-configuration.md`.

## Opt-in per project

Sprints, releases and burn-rate reports (burndown, velocity) are **not for every project**: many follow a different workflow. They are switched on per project in the config (`cadence: {sprints: true, releases: true}`); the `scrum` and `agile` presets switch them on, every other preset leaves them off. With a capability off, its data file is never created, its monitor views and report sections are hidden, and its commands refuse with the one line that turns it on.

## Out of scope

- Estimation techniques.