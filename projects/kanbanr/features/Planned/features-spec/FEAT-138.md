## Problem

The Releases page counts an item "finished" only at an end status. In the `scrum` preset that is Released, so a planned release reads "0/4 finished (0%)" while one of its items is Done — ready to ship, and counted as done by the sprint (FEAT-137). The page computes this in the browser with its own copy of the rule, which is how it drifted from the server's.

## Behavior

- An item counts as finished on the Releases page by the same rule as the cadence views: an end status, or a stage marked `done` (FEAT-137).
- The rule comes from the server, not a copy in the browser: the releases route reports each release's finished count, and the page shows it.

## Out of scope

- What `release cut` ships: it already ships the items that are Done.
