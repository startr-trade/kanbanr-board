## Problem

Starting an agile or Scrum project means designing statuses, gates and cadence by hand.

## Behavior

Presets `scrum` (Backlog → Ready → In Progress → Review → Testing → Done → Released, with DoR at Ready and DoD at Done) and `agile` (Plan → Design → Develop → Test → Review → Released); stage names assume no code. The setup interview offers them and, for sprint presets, asks sprint length, first start, capacity, release cadence and first version, then creates Sprint 1 and the first release and writes `process/working-agreement.md` rendered from the gates.

See the design doc `design/process-as-configuration.md`.

## Opt-in per project

Sprints, releases and burn-rate reports (burndown, velocity) are **not for every project**: many follow a different workflow. They are switched on per project in the config (`cadence: {sprints: true, releases: true}`); the `scrum` and `agile` presets switch them on, every other preset leaves them off. With a capability off, its data file is never created, its monitor views and report sections are hidden, and its commands refuse with the one line that turns it on.

## Out of scope

- Team ceremonies.