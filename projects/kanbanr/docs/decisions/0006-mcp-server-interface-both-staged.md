---
id: ADR-0006
status: accepted
date: 2026-06-12
affects:
- FEAT-005
- FEAT-023
quality:
- Compatibility
- Maintainability
trade_offs:
- gain: Compatibility
  cost: Maintainability
zachman:
- How
- Where
layer: logical
---

# MCP server interface: both, staged

## Context

kanbanr is driven by Claude through the **kanbanr skill**, which shells out to the local `kanbanr`
CLI. The CLI is the single writer: it links `kanbanr-core`, applies every mutation through the
`dispatch` router (`(method, path, body) → store op`), commits the git-backed data folder, and
pushes optional remotes. `kanbanr serve` runs a read-only, localhost view daemon over the same
folder, also via `dispatch`. There is no server in the write path, no accounts, no login.

The **Model Context Protocol (MCP)** is the dominant integration pattern for AI task tools (Task
Master AI, GitHub Projects, Linear and Jira all ship MCP servers). An MCP server would let *any*
MCP-capable agent — not just Claude Code with the skill — call kanbanr natively as tools, instead
of shelling out to a CLI. The question was explicit: skill+CLI only, MCP only, or both — decide
before building.

A hard constraint sits underneath it: kanbanr is **local-only by design** (ADR-0001). The writer is
"you on this machine"; there is no auth because there is nothing to authenticate against. Any MCP
surface inherits that process model — it must run locally, against the local data folder, as the
same single writer.

## Decision

We will adopt **both**, staged: ship a thin MCP server as an **additive, optional** surface, while
skill+CLI remains the primary, default path.

The skill+CLI path already works and is the differentiator — the behavioural contract in
`SKILL.md` is the moat, not the transport. Because `dispatch` is already the single source of truth
for data operations, an MCP shim over it is thin: it maps MCP tool calls onto the same
`(method, path, body)` shapes the CLI and daemon use, so all three agree by construction. Staging
it keeps the new surface off the critical path — if it does not earn its keep, it can be dropped
without affecting day-to-day use.

We explicitly do **not** make MCP the only or default interface, and do **not** turn it into a
remote or network service. It stays local, matching kanbanr's "you are this machine's user" model.

## Alternatives considered

**skill+CLI only (status quo).** Simple, already works, nothing new to maintain — but reach is
effectively Claude Code, and non-Claude MCP agents cannot call kanbanr natively.

**MCP replacing skill+CLI.** Broad agent reach, but it throws away the working, well-tested
skill+CLI path and the CLI's value as a human-usable tool, and the behavioural contract would have
to be re-encoded for MCP clients with no guarantee they honour it. High cost, real regression —
rejected outright.

## Consequences

Any MCP-capable agent can drive kanbanr natively; the implementation is thin because it reuses
`dispatch`; the proven skill+CLI path is untouched and stays the default. One binary, one engine,
three callers (CLI, view daemon, MCP) that agree by construction.

The cost is maintainability: one more interface to maintain, test and document, and a **second
place the behavioural contract must be conveyed** — which is the real risk, because a contract
stated twice drifts. There is also a stdio process model the host agent must launch and manage.

Unchanged and out of scope: MCP does not become a remote service, does not add auth or a
write-over-HTTP path, and does not replace the skill+CLI.

## Compliance

Not yet built — this decision is a commitment about shape, not shipped code. When it is built:
a `kanbanr mcp` subcommand on the existing binary, speaking MCP over stdio, linking `kanbanr-core`
and calling `dispatch` directly (no HTTP, no second validation path — transitions,
milestone-required, DAG cycles and referential integrity are already enforced in the engine). The
tool set mirrors `dispatch`'s write ops plus reads, including `batch` so an agent can bundle
changes into one commit. The check that it stayed thin is that it adds no validation of its own.

## Revisit when

- A concrete **non-Claude-Code MCP agent** becomes a real target — the clearest trigger to actually
  build this rather than having decided it.
- The skill+CLI path starts feeling like friction for agents that natively prefer MCP tools.
- kanbanr ever pivots toward teams or a hosted deployment, at which point the local-only
  constraint — and therefore this process model and the auth question — must be reopened, together
  with ADR-0001.
