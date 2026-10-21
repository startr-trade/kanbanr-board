# An item's code says what kind of work it is

## Why
On 22 Oct 2026 the user: "FEAT prefix confuses me on the type." Every item gets a `FEAT-` code
whatever its kind, so a defect, a chore or a docs change reads as a feature (FEAT-208 to FEAT-210
are defects, FEAT-206 a chore, FEAT-215 docs). The user also said work items for maintenance should
not read as features.

## Decided (22 Oct 2026, by the user)
- Prefix by kind: **FTR** feature, **DEF** defect (and the older `bug` kind), **MNT** chore
  (maintenance), **DOC** docs, **SPK** spike. Configurable per project; a project that sets none
  keeps `FEAT-` for everything, as today.
- **A counter per kind**: DEF-001, MNT-001, FTR-001, … (so DEF-012 and FTR-012 can both exist).
- **Existing codes are kept**: the 216 `FEAT-` items keep their codes (they are in commit trailers,
  branch names, links and the public board's history). Changing an item's kind later does not
  rename it.

## Design
_To be written and agreed before build._ It must cover every place a code is recognised or made:
allocation, the reference finder (Rust and the monitor's TypeScript twin, with their shared
fixture), branch names and the commit guard, `Refs:` trailers, git doctor, `why`/`trace`, routes and
the monitor's links, the CLI, docs and the skill — and that `FEAT-` keeps working everywhere.
