---
id: ADR-0005
status: accepted
date: 2026-09-25
deciders:
- Venkatraman B
affects:
- FEAT-053
- FEAT-047
- FEAT-033
driven_by:
- FEAT-053/R-7
quality:
- Compatibility
- Maintainability
trade_offs:
- gain: Compatibility
  cost: Maintainability
zachman:
- What
- How
layer: physical
---

# Reading a board never rewrites it

## Context

The board is plain YAML in a git repository, and every write is a commit. That makes a
reformatting write expensive in a way it would not be in a database: a new field that serializes
as `null` on every existing item rewrites hundreds of files, floods the history with noise, and —
when the mirror is enabled — re-pushes every linked issue.

Nine schema additions have landed since the format stabilised, and each one had the same
opportunity to do that.

## Decision

We will keep every new field optional and `skip_serializing_if` its empty value, so a board written
by an older version loads and re-serializes byte for byte. Reading a board — `board`, `feature
show`, `export`, `report`, `trace` — writes nothing at all.

## Alternatives considered

Migrating on load, stamping every file with the current schema — rejected: it turns a read into a
write and destroys the property that `git status` after a read is empty. Versioned parsers per
schema — rejected as far more machinery than a board of this size justifies.

## Consequences

Upgrades are invisible: a user pulls a new binary and their history stays clean. The cost is
maintainability — every new field needs the attribute, the three-place rule (struct, `meta()`,
`from_meta()`) has to be followed by hand, and a field added without the attribute would not be
caught by the compiler. The legacy-load check in the gates is what catches it instead, and it has
run on every item in this milestone.

## Compliance

The legacy invariant is a manual gate on every schema change: `kanbanr board && kanbanr feature
show FEAT-001` against the real data folder must leave `git status` empty in the board repo. It is
recorded as a test on FEAT-053/R-7 and was run for FEAT-053, FEAT-054, FEAT-055, FEAT-056 and
FEAT-057.
