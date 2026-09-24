# TDD test states, kanbanr check, TOGAF workflow preset

## Problem
A test entry with no lifecycle is an assertion, not evidence; and a project wanting TOGAF phases as columns has to type six statuses by hand.

## Behavior
- `store::set_test_state{,_on}` and a `test.state` batch op mirroring `task.state`, so a red->green flip is one tiny op that never rewrites prose.
- `kanbanr test state <CODE> <R-n> <name> green`; `kanbanr check [CODE] [--file]` reporting gaps for one item or a PR-supplied definition, with `--json`.
- `config::togaf_preset` (Vision -> Business Arch -> System Design -> Implementation -> Migration -> Operations, Operations terminal) via `project init --workflow togaf` and `config workflow --togaf`.

## Out of scope
A `togaf_phase` field — the status is the phase.
