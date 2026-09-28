---
id: ADR-0007
status: accepted
date: 2026-09-28
deciders:
- Venkatraman B
affects:
- FEAT-030
- FEAT-041
- FEAT-074
driven_by:
- FEAT-074/R-5
quality:
- Security
- Maintainability
trade_offs:
- gain: Security
  cost: Functional Suitability
zachman:
- Where
- Who
layer: conceptual
---

# A data folder is the sharing and visibility boundary

## Context

A kanbanr data folder holds `projects/<id>/…` and can hold many projects. Two features depend on
that co-location: the portfolio view and cross-project dependencies both read one `projects/`
directory, resolving qualified references like `other:FEAT-012` within it.

The same folder is one git repository, and sharing a board means adding a remote to it. Git's
access control granularity is the **repository**: there is no per-path write control, and
CODEOWNERS gates review rather than push. So everything in a data folder shares one set of people
who may read it and one set who may write it.

Those two facts pull against each other. Co-locating projects is what makes the cross-project view
possible, and it is also what forces them to share visibility and write access. Nothing in the
layout said so, which is how a private project could end up beside a public one without anyone
noticing until the remote was added.

## Decision

We will treat a data folder as the **sharing and visibility boundary**. Projects co-located in one
folder must share both the audience that may read them and the set of people who may write them.

Where those differ, the projects belong in separate data folders — one repository per access set,
which is the granularity git actually grants. The cross-project view across such folders is a
separate concern, designed as FEAT-074 and deliberately not built yet.

## Alternatives considered

**Per-path access control inside one repository.** Not available: git has no such thing, and
CODEOWNERS is a review mechanism, not a push mechanism.

**A submodule per project**, giving each its own repository while keeping one folder. Git can
express it, but it breaks the single-writer model — the CLI opens the data folder, stages
everything and commits, so a write inside a submodule leaves the real change uncommitted there and
only a gitlink in the superproject. It also puts submodule friction on every contributor's clone to
serve a view only a maintainer needs.

**Building FEAT-074 now**, so visibility never constrains layout. Rejected as premature rather than
wrong: today the projects in question are both public, and the contributors who differ between them
do not write boards at all — a contribution's definition travels in its pull request and is
ingested on merge. The population needing differentiated board write access is currently empty.

## Consequences

Sharing a board is a decision about every project in its folder, and that is now something the
layout states rather than something discovered when a remote is added. Grouping by audience keeps
the rule simple: if you would not publish these projects together, they do not belong together.

The cost is functional suitability. A portfolio view cannot span an access boundary, so a team
working across projects of differing visibility gets no rollup across them until FEAT-074 is built.
That is a real loss and the reason the item stays defined rather than discarded.

One consequence is worth stating plainly because it is expensive: separating a board **after**
publishing means rewriting history in a repository other people have cloned. Co-locating projects
of differing visibility "for now" is therefore not a reversible convenience.

## Compliance

`kanbanr remote add` operates on the data folder, so the boundary is enforced by where a project
lives rather than by a check. What can be checked is the consequence: under FEAT-074, a dependency
naming a project outside the reader's workspace is reported as external rather than as broken, and
recording one is refused by default — `doctor::tests::a_reference_outside_the_workspace_is_unverifiable_not_broken`.

## Revisit when

- A project of **different visibility** joins the others — private client work beside public
  projects. This is the likeliest trigger.
- An outside contributor should write a board **directly**, rather than contributing through a pull
  request whose definition is ingested on merge.
- Employees become project-scoped, so someone may write one project's board and not another's.

Any of these makes FEAT-074 concrete rather than speculative, and it is defined and waiting.
