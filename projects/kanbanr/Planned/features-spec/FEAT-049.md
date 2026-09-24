# EARS + ISO 25010 validation and doctor gap checks

## Problem
Requirement text and quality tags are free strings; nothing tells the author a requirement is unusable or untestable, and a naive check would flood the report with 40 completed legacy items.

## Behavior
- `validate::next_key(prefix, existing)`; `classify_ears` for the five patterns (case-lenient, never rejects); the nine ISO 25010 characteristics with `normalize_iso_tag`.
- `doctor::scan_definitions` gated by terminal status, then `displayed_states`, then `charter.adopted_at` — 45 items to 4 on kanbanr's own board.
- One aggregated message per item; per requirement: not EARS, no test, NFR missing ISO tag or measured scenario; INVEST reduced to `estimate_days > 3` and no tests.
- Unsupported claims are reported: a `measure` that names no test, an ISO tag with no scenario. Blank beats invented — the skill leaves gaps for doctor to flag.
- Kind-specific shapes resolve from `kind`; blank/unknown kind resolves to the strictest (feature). A per-item `exempt: "<reason>"` escape stays recorded.

## Out of scope
Storing derived patterns or [MISSING: ...] markers — both are rendered, never stored.
