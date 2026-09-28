# Defect: two outputs that train the reader to ignore them

## Problem
On kanbanr's own board `kanbanr report` prints `cycle time (days): p50 0.0 p90 0.0 max 0.0` for work that took hours, and then lists 27 requirements as stale evidence — every green recorded before the most recent commit.

## Root cause
- Cycle time is always rendered in days, so anything under a day rounds to 0.0 and reads as a broken metric rather than as fast work.
- Staleness is `checked_rev != HEAD`. In a repo where every commit moves HEAD, all evidence is stale the moment anything is committed, so the warning fires on everything and clears on the next full test run. A check that always fires is one people learn to skip — this codebase says so in several comments, and then shipped one.

## Behavior
- Durations under a day are shown in hours; the unit is stated either way.
- Stale evidence is summarised (how many, and the oldest), naming at most a few items, with the instruction that re-running the suite refreshes it.

## Out of scope
Changing what counts as stale.