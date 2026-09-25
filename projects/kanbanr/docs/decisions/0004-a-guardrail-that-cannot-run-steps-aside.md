---
id: ADR-0004
status: accepted
date: 2026-09-25
deciders:
- Venkatraman B
affects:
- FEAT-056
- FEAT-053
- FEAT-044
driven_by:
- FEAT-056/R-9
- FEAT-057/R-8
quality:
- Reliability
trade_offs:
- gain: Reliability
  cost: Functional Suitability
zachman:
- How
layer: logical
---

# A guardrail that cannot run steps aside rather than blocking

## Context

kanbanr installs itself into other people's workflows: git hooks in their repository, Claude Code
hooks in their settings, a capture hook on every Bash command. Each of those runs in conditions we
do not control — a fresh clone with no kanbanr on PATH, a CI runner, a colleague who never
installed the tool, a directory that is not a kanbanr project at all.

A check that fails closed in those conditions does not protect anything. It makes the repository
unusable for someone who never opted in, and the first thing they will do is delete the hook or
pass `--no-verify`, which removes the check permanently.

## Decision

We will make every guardrail degrade to silence when it cannot do its job. The git hooks exit 0
when `kanbanr` is not on PATH. The commit checks pass when no board is reachable. The capture hook
records nothing when it recognises no test output. `doctor` warns and never fails a write. Only
two things refuse: a reference that names something the board does not have, and a commit that
names nothing at all — both of which the author can fix in the message they are already writing.

## Alternatives considered

Failing closed on any uncertainty — rejected: it converts a missing dependency into a broken
repository, and teaches bypassing. Warning on stdout instead of blocking, everywhere — rejected
too: a check that never refuses is a check people stop reading, which is the failure recorded in
lesson L-4.

## Consequences

The tool is safe to install in a shared repository: someone without kanbanr sees no difference.
The cost is functional suitability — the guarantee is weaker than it looks, because a commit made
on a machine without the CLI carries no reference and nothing notices at the time. `kanbanr doctor`
and `kanbanr trace` are what catch it afterwards, which is why both report unreferenced work
rather than assuming the hooks caught everything.

## Compliance

`scm::tests::hooks_install_without_clobbering_what_was_there` asserts the installed hook carries
its `command -v kanbanr >/dev/null 2>&1 || exit 0` guard; `cli_git_guardrails_in_a_scratch_repo`
exercises what does refuse and what does not.
