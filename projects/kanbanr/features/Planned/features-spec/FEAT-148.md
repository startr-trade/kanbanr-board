# The 1.0 stability policy

## Problem
1.0.0 promises that what users rely on will not break before 2.0, but nothing says what that is.
Without a written surface, "1.0" tells a user nothing they can depend on, and a maintainer cannot
tell whether a change needs a major version.

## Behavior
A docs chapter, `docs/src/project/stability.md`, stating:
- **Covered from 1.0:** the board's on-disk format (folders, YAML fields, `schema_version`), each
  project's `config.yaml`, the `.kanbanr` marker; CLI commands, flags, exit codes and `--json`
  output; the monitor's read API; the skill's hooks and the commit trailer format.
- **Not covered:** human-readable CLI text, the monitor's look, the docs, internal crates.
- **How things change:** additive changes in minor versions; a deprecation is announced in one minor
  release and removed only in the next major; an older binary refuses a newer board rather than
  misreading it (already true); a board written by 1.x opens in every later 1.x.
- Linked from the README, the installation chapter and CONTRIBUTING, and named in an ADR.

## Out of scope
Tooling that detects a breaking change automatically.
