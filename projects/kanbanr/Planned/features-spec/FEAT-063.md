# Defect: the retro claims more than the board recorded

## Problem
The Stop hook demanded retrospectives for MS-001, MS-003 and MS-005 — waves that finished months before the method was adopted. Running them shows why that is wrong:

- MS-001 reports no recorded moves for any of its three items, so there is nothing to retrospect. A narrative written from it would be invention.
- MS-003 and MS-005 report `cycle time: p50 5m` and `p50 19m`. Those numbers come from the activity-log fallback, which measures the gap between **board writes**, not how long work took. Items bulk-edited in one sitting look like minutes of work.
- Both also print `ran: 2026-06-12 → still running` for waves where every item is finished, because with no history there is no finish timestamp to show.

## Root cause
Three places where the retro speaks with more confidence than its evidence supports: `due` has no notion of a wave the board never watched; the activity-log fallback's durations are mixed into the same percentiles as real transition history; and a missing finish timestamp is rendered as "still running" rather than as unknown.

## Behavior
- A wave with no recorded transitions on any item is not due a retrospective, and says why if asked for one directly.
- Durations derived from the changelog are reported separately as approximate, never mixed into cycle time.
- A finished wave with no finish timestamp says the date is unknown, not that it is still running.

## Out of scope
Reconstructing history for items that finished before it was recorded.