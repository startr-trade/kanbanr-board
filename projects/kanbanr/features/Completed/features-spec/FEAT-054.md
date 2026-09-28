# Wave retrospectives

## Problem
Waves grow while they run — defects found inside a wave are added to it — so a plain 'we finished 12 items' hides that four were defects the wave injected.

## Behavior
- `kanbanr retro <milestone | --since 14d | --label x>`: scope growth split by cause (defect / newly discovered / split), defects introduced_by wave items and how many escaped, cycle time p50/p90, rework as Completed->active back-transitions, requirements with green tests at completion, stale `checked_rev`, estimate vs actual.
- A narrative retro written from those numbers plus the changelog and git log, stored as a kanbanr doc linked to the milestone; computed facts and narrative kept visibly separate.
- Triggers: on demand, a sliding window, and wave completion via a milestone-completed event surfaced by the Stop hook.
- Best-effort backfill of pre-history items from `activity.yaml` move entries.

## Out of scope
Charting in the monitor.
