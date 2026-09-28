# Defect: a stale reader shows no data rather than an error

## Problem
FEAT-071 moved item files from `projects/<id>/<Status>/` to `projects/<id>/features/<Status>/`. A `kanbanr serve` process started before that change looks in the old location, finds nothing, and serves a board with zero items. The user saw an empty dashboard — including no Completed items — and reasonably read it as data loss.

The new code reads either shape, so an upgraded binary is fine. The problem is the other direction: an older reader has no way to know the board moved, because the layout change did not bump `CURRENT_SCHEMA_VERSION`. Silence is indistinguishable from emptiness.

This is the third stale-process failure in one session — a cached `index.html` presented as diagrams not rendering, a guard built but never registered, and now this. Each looked like a different bug.

## Behavior
- A layout or storage change bumps the schema version, so a board records which shape it was written in.
- A reader that encounters a project whose `schema_version` is **newer than it understands** says so — plainly, naming the upgrade — rather than reporting an empty or partial board.
- Reading an older board keeps working unchanged; that direction is already handled by accepting both shapes.
- `kanbanr serve` says it too, at startup and in the API, so the monitor can show it instead of an empty page.

## Out of scope
Making an old binary able to read a new layout. The point is to fail loudly, not to be forward-compatible.