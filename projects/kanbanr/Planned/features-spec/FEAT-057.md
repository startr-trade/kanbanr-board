# Code tied to the why: trace, why, ADRs, Zachman matrix

## Problem
Code can be traced to an item at best, never to the requirement or decision that justifies it, and architecture decisions sit outside the graph entirely.

## Behavior
- Every node reaches a goal: item->goals, requirement->item, test->requirement, defect->violates + introduced_by (chains allowed, cycle-checked), doc->refs, ADR->affects/driven_by, code/commit->annotation + trailer.
- The manifest is canonical and validated (unknown id = error); inline annotations `(FEAT-046 R-2)` are a derived convenience on the unit that owns the behaviour; the trailer is the durable machine link; blame is the fallback; `kanbanr trace --json` generates the traceability manifest rather than storing one.
- `kanbanr trace <CODE|R-n|G-n>` downward, naming gaps; `kanbanr why <path>[:line]` upward, printing code -> requirement -> goal -> charter purpose.
- ADRs stay documents with front-matter joining the graph (`affects`, `driven_by`, `quality`, `trade_offs`, `zachman`, `layer`, `supersedes`/`superseded_by`); body sections scaffolded by `adr new`: Context, Decision, Alternatives, Consequences, Compliance; `adr supersede` writes both documents in one commit, flips the old status and lists affected items; `adr history` walks the lineage.
- `trace --zachman` renders the derived columns x layer matrix, reporting gaps.
- Doctor orphan checks: an item that cannot reach a goal, a requirement with no test or no code evidence, a defect naming nothing it violates, a doc referencing nothing, an ADR affecting nothing, code referencing a superseded ADR, an NFR with a measure but no ADR.

## Out of scope
Rewriting history to add trailers to past commits.
