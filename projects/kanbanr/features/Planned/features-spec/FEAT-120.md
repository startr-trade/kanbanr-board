## Problem

There is no release: finished items are not grouped into what shipped, and feedback cannot point at a version.

## Behavior

`projects/<id>/releases.yaml` (version, target, state, shipped_at, tag, notes_doc, carried); `release` on an item; `kanbanr release add|plan|cut`; cut moves planned Done items to the terminal status through its gate, writes `releases/<version>.md` from their statements and requirements, optionally tags the repo, and carries unfinished planned items; `feature add --found-in <version>`; an `in_release` check.

See the design doc `design/process-as-configuration.md`.

## Out of scope

- Deployment.