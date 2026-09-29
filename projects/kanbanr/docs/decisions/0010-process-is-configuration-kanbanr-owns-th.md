---
id: ADR-0010
status: accepted
date: 2026-09-29
deciders:
- Venkatraman B
affects:
- FEAT-113
- FEAT-114
- FEAT-115
- FEAT-116
- FEAT-117
driven_by:
- FEAT-113/R-4
- FEAT-113/R-5
quality:
- Maintainability
- Flexibility
zachman:
- How
- When
layer: logical
---

# Process is configuration: kanbanr owns the checks, the project owns the process

## Context

kanbanr's guardrails were written for one shape of work: agree, start, finish. The start gate
asked for approval on any move into a status that meant work had started. `finish` checked one
fixed list and jumped to the first end status. Auto-advance looked for a status literally named
"Completed". The rules for what an item was missing were written five times over and had drifted.

Projects follow different processes: TOGAF phases, PDCA cycles, design-control flows, an
organisation's own quality system. Each asks different things at different stages. Under TOGAF on
a real board (katalog), the phases were only column names. Approval was demanded at every move,
the branch was made at Business Arch, and `finish` could not end from Implementation. Supporting
each process in code would make kanbanr a catalogue of methodologies, and still miss the one a
given organisation uses.

The qualities at stake are maintainability (one place for each rule) and flexibility (a new
process without a new release), without weakening the guardrails. A gate a process cannot express
gets bypassed, and a gate an older binary ignores is worse than none (ADR-0004).

## Decision

kanbanr provides a closed, versioned vocabulary of checks it can evaluate from board data
(`readiness.rs`), plus named sign-offs for conditions it cannot see. A project's workflow declares,
per status, which checks and sign-offs entering that status requires or warns about, whether a
failure blocks or warns, and what happens on entry, such as making the branch. Presets (default,
scheduled, togaf, pdca, design-control) are data files in exactly that format, and an
organisation's own process loads the same way. Every surface asks the one engine: the move path,
auto-advance, `start`, `finish`, `check`, `doctor`, the review queue, the monitor and CLAUDE.md.
A workflow that declares no gates gets today's rule, synthesised, so no existing board changes.

## Alternatives considered

- **A process type hard-coded per methodology** (a TOGAF mode, a PDCA mode). It adds code for
  each process, still can't express an organisation's own, and turns every change of process into
  a release.
- **Script checks: a gate runs a command and passes on exit 0.** Powerful, but the board would
  depend on a code checkout and its tools, and would run arbitrary commands. Named sign-offs cover
  what the board can't see, as a recorded human agreement, and run nothing.
- **Warn only, never block.** The failure this project exists to prevent is work built on
  reasoning nobody agreed to. Warnings alone let that happen. Enforcement is instead chosen per
  gate, blocking by default, with a recorded override.
- **Keep one gate (approval) and document processes in prose.** Prose is not enforced, and a stage
  that can't say what it needs gets everything asked up front, or nothing.

## Consequences

- **What it buys:** A new process is a YAML file, not a release. Definitions grow stage by stage,
  and each surface says what the next stage needs. The five drifting copies of the rules are one.
  Sign-offs give auditable records for stages kanbanr can't observe.
- **What it costs:**
  - The check vocabulary is a public contract: a check can be added, but renaming or removing one
    breaks every process file that names it.
  - A board with gates is stamped `schema_version: 3`, so older binaries refuse it. That is
    deliberate, but it is friction for anyone mixing versions.
  - Declared gates replace the synthesised rule entirely. A process that forgets `approved` on
    its working stages drops the approval gate there, and that is the author's call to make.
  - Legacy behaviour holds only while no gates are declared. The "Completed" name is recognised
    as terminal only when a workflow declares no terminal states.

## Compliance

- `effective_gates_reproduce_the_legacy_gate`: with no gates, the synthesised rule makes exactly
  the old decisions.
- `readiness_is_one_answer_across_surfaces`: the endpoint, `check`, `doctor` and the query agree.
- `unknown_gate_names_are_rejected`: a gate that could never match is refused when the workflow is
  saved.
- `presets_apply_with_their_gates`: every preset passes the same validation as a hand-written
  workflow.
- Doctor warns when a board's schema is older than its content needs, and a reader refuses a
  schema newer than it understands.
