---
id: ADR-0002
status: accepted
date: 2026-09-25
deciders:
- Venkatraman B
affects:
- FEAT-057
- FEAT-050
driven_by:
- FEAT-057/R-3
quality:
- Maintainability
trade_offs:
- gain: Maintainability
  cost: Performance Efficiency
zachman:
- How
layer: logical
---

# The traceability view is derived, never stored

## Context

Every link this project needs already exists somewhere authoritative: an item names its goals, a
requirement belongs to an item, a test belongs to a requirement, a decision names what it affects,
and a commit trailer names what it serves. FEAT-057/R-3 asks for a view across all of them.

The obvious implementation is a traceability manifest — a file listing the links, regenerated when
something changes. Standards work often expects exactly that artifact.

## Decision

We will derive the whole traceability view on demand and store none of it. `kanbanr trace --json`
generates the manifest for a CI run or an audit; nothing writes it back to the board.

## Alternatives considered

A stored `traceability.yaml`, regenerated on write — rejected: it is a third copy of links that
already exist in two places, and the copy that goes stale first, because nothing fails when it is
out of date. A cached index invalidated on write — rejected as the same thing with extra
machinery; the board is small enough that the question does not arise.

## Consequences

The view cannot disagree with the board, which is the property that matters: a reader who prints a
trace is reading the same data the checks read. Deleting a reference removes it from the view with
no second edit. The cost is performance efficiency — every trace re-reads the project, its
decisions and its documents — and it is a cost we can afford only because a board is hundreds of
items rather than millions. If that ever stops being true, this decision is the one to overturn,
and a cache would be the way to do it.

## Compliance

`trace::tests::tracing_downward_reports_the_chain_and_its_gaps` builds a trace with no stored
index and asserts the chain and its gaps; the module carries no write path at all, so storing one
would require adding it deliberately rather than by drift.
