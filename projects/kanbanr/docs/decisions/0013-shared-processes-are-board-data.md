---
id: ADR-0013
status: accepted
date: 2026-10-05
deciders:
- Venkatraman B
affects:
- FEAT-169
- FEAT-170
- FEAT-171
driven_by:
- FEAT-169/R-3
zachman:
- where
- who
layer: logical
decided: 2026-10-05
---

# Shared processes are board data

## Context

A process (statuses, moves and gates) was copied into each project that applied it, and lived
nowhere else. A team wanting one agreed way of working copied the YAML between projects and
between people by hand, and the copies drifted. A process needs one home that the team reads, that
changes with a record, and that every project can be compared against. kanbanr already has a
sharing boundary: the board is a git repository, and its remote decides who has it (charter
constraint: sharing happens through a git remote, which is also the access boundary).

## Decision

We keep shared processes on the board, as `processes/<name>.yaml` beside `projects/`, saved by
`kanbanr process save` in one board commit. They reach the team through the board's remote, like
every other part of the board. A personal library, `~/.kanbanr/processes/`, exists only to carry a
process from one board to another. The CLI reads it, never the board. A name is looked up on the
board, then in the personal library, then among the built-in processes. Each project records the
process it applied (name, library, version and content rev). A change to a saved process is
reported to the projects using it, and reaches each one only when its user runs
`kanbanr process update`.

## Alternatives considered

- **A process registry or server.** A second system to run and secure, against the charter's "no
  server required"; and its access rules would duplicate the board's remote.
- **Personal library only.** One person's copy cannot be the team's agreement, and every teammate's
  copy drifts on its own.
- **A project as the source** ("copy project A's workflow"). Ties the process to one project's
  history, and an edit made for that project would silently become everyone's.
- **Apply changes to every project automatically.** Moves items' gates under work in flight
  without anyone deciding; the user chose report-then-update-on-request.

## Consequences

- One process, versioned, reviewable in the board's git history, with the projects that use it
  listed by `process list`.
- A personal process used by a project can be compared only on its owner's machine; the board
  names it but cannot check it.
- Updating is a per-project decision, so projects can lag; doctor, the session start and the
  monitor say so until someone decides.
- `processes/`, the file's `process:` header and the project's `process:` record join the stable
  surface at 1.0 (ADR-0012).

## Compliance

- `a_teammate_clone_applies_the_boards_process` (FEAT-169/R-3): a clone of the board lists and
  applies the saved process with nothing in the teammate's home folder.
- `a_name_resolves_board_then_personal_then_builtin` (FEAT-169/R-2), and
  `update_applies_on_request_and_keeps_occupied_statuses` (FEAT-170/R-3).
- The board itself never reads a home folder: `kanbanr_core::Store` has no access to the personal
  library, which is `kanbanr_core::library` called only from the CLI.
