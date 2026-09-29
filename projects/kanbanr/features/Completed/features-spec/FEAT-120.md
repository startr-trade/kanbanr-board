## Problem

There is no release: finished items are not grouped into what shipped, and feedback cannot point at a version.

## Behavior

`projects/<id>/releases.yaml` (version, target, state, shipped_at, tag, notes_doc, carried); `release` on an item; `kanbanr release add|plan|cut`; cut moves planned Done items to the terminal status through its gate, writes `releases/<version>.md` from their statements and requirements, optionally tags the repo, and carries unfinished planned items; `feature add --found-in <version>`; an `in_release` check.

See the design doc `design/process-as-configuration.md`.

## Opt-in per project

Sprints, releases and burn-rate reports (burndown, velocity) are **not for every project**: many follow a different workflow. They are switched on per project in the config (`cadence: {sprints: true, releases: true}`); the `scrum` and `agile` presets switch them on, every other preset leaves them off. With a capability off, its data file is never created, its monitor views and report sections are hidden, and its commands refuse with the one line that turns it on.

## Out of scope

- Deployment.