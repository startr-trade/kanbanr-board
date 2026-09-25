# Defect: the retro's two counts are wrong

## Problem
Run against kanbanr's own MS-006, `kanbanr retro` reported "1 to begin with, 11 added" for a wave whose twelve items were all planned together, and "1/23 requirements proven" for a wave in which three items have every requirement green.

## Root cause
Two separate mistakes:

1. **Wave start.** `first_move` falls back to `created_at` when an item has no transitions, so the wave's start time became the earliest item's *creation*. Every other item of the same planning batch was created microseconds later and therefore counted as growth. The wave begins when work begins, not when the first item was written down.
2. **Evidence.** The retro required `checked_rev == HEAD` to count a requirement as proven. A retrospective is a historical account: evidence recorded during the wave is what it should measure. Staleness against HEAD is `kanbanr report`'s job, and re-using it here made every requirement proven before the last commit disappear.

## Behavior
- The wave starts at the first recorded *transition* across its items; with no transitions at all, nothing is growth.
- The retro counts a requirement as proven when a test was recorded green, regardless of the revision.

## Out of scope
Changing what `kanbanr report` means by stale evidence.