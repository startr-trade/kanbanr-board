---
id: ADR-0012
status: proposed
date: 2026-10-02
affects:
- FEAT-148
- FEAT-150
driven_by:
- FEAT-148/R-1
---

# Stability: what 1.0 keeps compatible

## Context

1.0.0 is a promise that what users build on will not break before 2.0. kanbanr's users build on
more than a CLI: a board is files they keep for years and share through git; scripts and CI parse
`--json` and exit codes; the Claude Code hooks call the CLI; the monitor's API is read by the
browser and could be read by anything. Until now none of this was written down, so neither a user
nor a contributor could tell whether a change was compatible. The features are frozen until 1.0
(FEAT-147) precisely so this surface can settle first.

## Decision

We keep stable, from 1.0 until 2.0: the board's on-disk format and documented fields, each
project's `config.yaml` (gates and their check vocabulary included), the `.kanbanr` marker, every
documented CLI command and flag, exit status (zero on success, non-zero on failure, `check`
non-zero on gaps), every `--json` field, the monitor's `/api/…` endpoints and fields, the commit
trailer and the hook commands. Human-readable output, the monitor's look, the skill's wording, the
internal crates and anything undocumented are not covered. Additions come in minor versions; a
board that needs a newer kanbanr says so in `schema_version` and an older one refuses it; anything
stable is deprecated in a minor release, with a warning, before it is removed in a major one. The
policy is published as `docs/src/project/stability.md`.

## Alternatives considered

- **No written policy; "semver" in the README.** Leaves "what is the public API?" to each reader;
  for a tool whose main artifact is files on disk, that answer is not obvious, and a contributor
  could break a board while believing they changed nothing public.
- **Covering the human-readable output too.** Would freeze every message and table, making the CLI
  impossible to improve; `--json` exists so that machines need not parse prose.
- **Covering the internal crates as libraries.** Nothing outside this repository depends on them,
  and promising their API would slow every internal change for no user.

## Consequences

Users can script against the CLI and keep boards across upgrades with confidence; contributors
have a list to check a change against. The cost is that a design mistake in a stable surface is
kept until 2.0, so the freeze before 1.0 matters. Writing the policy exposed one hole, now closed
(FEAT-151): an older kanbanr rewriting a board file used to drop fields only a newer version
knows; it now writes them back unchanged, so machines sharing a board can run different 1.x.

## Compliance

The changelog and the item of any change to a stable surface say so (the contributing guide asks
for it). Before 1.0 is tagged, FEAT-150 records that no stable surface broke during the freeze.
The board format is guarded in code: `schema_version` makes an older binary refuse a newer board.

