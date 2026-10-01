## Problem

The README still introduces kanbanr as it was before MS-006 to MS-008: "a kanban-based task manager", a model of feature items, milestones and todo-lists. It says nothing about what the project now is for and does — the method (a statement, goals, Zachman, EARS requirements with named tests, approval pinned to content), process as configuration (presets, gates, sign-offs, overrides), opt-in sprints and releases with a burndown, traceability (`kanbanr why`, commit trailers, the git and Claude Code guards), the plan-mode setup, or the CI and security gates. A visitor cannot tell why to choose it. The architecture chapter likewise describes none of the readiness engine, gates or cadence, and a few commands (`sprint list`, `release list`, `config rename-status`) appear in no page.

## Behavior

- **README, rewritten for a first-time visitor:** the lockup (FEAT-133), a one-line pitch and badges; *why* (the plan, reasoning and evidence otherwise live only in a transcript); *what you get* in a handful of points (system of record recovered every session; the method; process as configuration; sprints and releases, opt-in; traceability from goal to line; the live read-only monitor; local-first, git-backed, one binary); the new screenshots; a quick start (installer one-liner, then "set up kanbanr" in Claude); how it works (the architecture diagram); and links to the docs site, contributing and licence. Reference detail (data model, repository layout, test tiers) moves to the docs, linked.
- **Docs:** the architecture chapter gains the readiness engine, gates and sign-offs, and cadence (sprints, releases, derived burndown); `sprint list`, `release list` and `config rename-status` are documented; the docs changelog stays in sync.
- Every claim in the README names a command or a page that shows it.

## Out of scope

- New screenshots and the logo themselves (FEAT-133).
