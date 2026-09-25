---
id: ADR-0003
status: accepted
date: 2026-09-25
deciders:
- Venkatraman B
affects:
- FEAT-057
quality:
- Maintainability
trade_offs:
- gain: Maintainability
  cost: Functional Suitability
zachman:
- What
- How
layer: conceptual
---

# Decisions are documents, not work items

## Context

kanbanr already has a unit of work with a lifecycle: the feature item, with an estimate, a branch,
an approval gate, requirements, tests and flow metrics. An architecture decision needs to join the
same graph — it is part of the reasoning — but it has none of those things.

## Decision

We will keep architecture decisions as **documents** in the board's `decisions/` folder, and give
them front-matter so tooling can follow them. Deciding is still work: it is a *task* on the item
that needed the decision, and the ADR is that task's output.

## Alternatives considered

Modelling an ADR as a feature item of kind `decision` — rejected: it would enter the flow metrics
and distort cycle time, and the approval gate would demand requirements and tests that a decision
does not have. A separate top-level entity with its own storage and routes — rejected as a third
concept to explain, when a document with front-matter already reaches every consumer (doc tree,
search, the monitor's Docs tab).

## Consequences

Decisions stay where prose belongs and are read like prose, while `affects` and `driven_by` make
them first-class in the graph. Metrics stay honest, because nothing that is not deliverable work
counts as an item. The cost is functional suitability: a decision has no board status, no owner
field and no gate, so "who still has to agree to this" is answered by the `status` field and the
review that produced it rather than by the tool.

## Compliance

`adr::tests::a_decision_round_trips_with_its_front_matter_and_sections` pins the storage shape;
`doctor` warns when an accepted decision affects nothing, or is missing its Decision or
Consequences section, which is what stops a scaffold from passing as a record.
