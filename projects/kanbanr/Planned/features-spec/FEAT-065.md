# The board governs the agent

## Problem
A project's instructions to Claude live in CLAUDE.md and `.claude/` hooks; the project's reasoning lives on the board. Nothing connects them, so either the instructions restate the charter — and drift from it within a week — or they omit it and the agent never sees the non-goals it should not propose against.

Separately, the rule that documentation belongs on the board (FEAT-040) is enforced only by the skill's prose, which is to say by good intentions.

## Behavior
- `kanbanr claude sync` writes a marked, regenerable block into the project's CLAUDE.md: purpose, goals, non-goals, constraints and the commands to run first. Marked so it is refreshed rather than hand-edited; everything outside the markers is left alone.
- The block REFERENCES the board rather than restating it in detail — a duplicate of live state is wrong the moment something moves.
- A PreToolUse guard on Write/Edit catches a markdown file being written into the project folder when the board is the system of record, and names the `kanbanr doc add` equivalent. Deliverable documentation (README, CHANGELOG, docs/, LICENSE and the like) is allowed.
- Prose is surfaced, never enforced: non-goals and constraints appear as context, and nothing blocks on them (ADR-0004).

## Out of scope
Inferring blocking rules from prose, and editing the user's global CLAUDE.md.