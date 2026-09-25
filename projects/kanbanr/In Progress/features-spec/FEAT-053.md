# Measurement: transition history, defects, test capture hook, report

## Problem
The board records intent but little evidence: no per-item state history (so no cycle time), no defect model (so no escape rate), and nothing captures that tests actually ran.

## Behavior
- `history[{at, from, to}]` appended on moves — cycle time, time-in-status, WIP aging, rework detection.
- The defect block wired to metrics: `severity`, `violates`, `introduced_by` (item or commit, chains allowed and cycle-checked), `found_in`, `root_cause`, `escaped`, `fixed_by`.
- A PostToolUse hook parsing `cargo test`/`npm test` output that flips TDD state with `checked_rev`, registered by `kanbanr hooks install`; never self-reported.
- `kanbanr tests --write` flags test names that no longer exist (modelled on `run_sources`); `kanbanr report --since` for throughput, cycle time p50/p90, WIP, escape rate, requirement coverage.

## Out of scope
Executing project-declared verify commands from the data repo.
