# Approval gates: review, approve, start gate, merge gate

## Problem
Three subagents and a coordinator spent seven hours and merged to main before anyone agreed the why; the work was then rejected. Recording the why and warning later would not have prevented it.

## Behavior
- `definition.approval{by, at, rev}` where `rev` is a stable hash of the definition; editing the definition lapses the approval.
- `kanbanr review <CODE>` renders the one-screen decision brief; `kanbanr approve <CODE>` records approval.
- Start gate: entering a non-default active status without a current approval is refused, naming what is missing; `--unapproved <reason>` is recorded, never silent.
- Merge gate: `kanbanr finish` refuses requirements added after approval, requirements without a green test, and commits referencing no requirement.
- Skill contract: scope -> define -> present brief -> wait for approval -> then code. Coordinators pass the approved definition to subagents, which return definition changes rather than unapproved code.

## Out of scope
Branch creation and commit trailers (FEAT-056).
