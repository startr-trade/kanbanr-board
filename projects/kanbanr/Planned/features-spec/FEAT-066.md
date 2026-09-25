# Defect: capped logs lose raw data

## Problem
`activity.yaml` and `events.yaml` are ring buffers capped at 200 entries: every append rewrites the file and truncates the oldest entry out of existence. On this board the activity log has been at the cap for some time, so everything older than the last 200 board writes is gone from the file.

This contradicts the charter constraint that raw data is never discarded, and it has one concrete consequence already visible: `retro.rs` asks for 1000 activity entries to reconstruct history for items that predate transition recording, and can never receive more than 200. That is why MS-001 reports "no recorded moves" for every item — its entries were trimmed away long ago, not never written.

A second effect is on the repository rather than the file: rewriting the whole log on every write means each board commit carries a diff of the entire tail, and the board repo has 2,269 loose objects in 240 commits with no pack.

## Behavior
- The raw logs are append-only and complete. Nothing is discarded by the writer.
- Files stay small enough that a write does not rewrite a large one — rotate by period (e.g. `activity/2026-09.yaml`) rather than truncating, so an append touches only the current segment.
- Reads take a limit and walk segments newest-first; the CLI, the monitor and the retro fallback keep showing a bounded window. The **view** is capped, never the data.
- `retro` can then actually reach the history it asks for, and says plainly when a period predates the log rather than reporting silence as absence.
- Migration keeps what exists: the current file becomes the first segment, and history already committed to git stays where it is.

## Out of scope
Reconstructing entries already trimmed away — they are in the board repo's git history, and mining commit diffs to rebuild a log would be a different feature with a much weaker guarantee.

## Note
Housekeeping on the board repo (`git gc`) is unrelated to this and is not a substitute: it compacts storage, it does not restore trimmed entries.