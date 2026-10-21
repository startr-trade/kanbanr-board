# The skill states what each sub-agent may do

## Why
On 21 Oct 2026 the user set the rule for sub-agents: "never write to the board is not the answer.
We need boundaries defined for the sub-agents precisely so that they do what is supposed to be
allowed for them to do", and asked for the skill to carry it, so that it applies to every project
using kanbanr. Today the skill says only "subagents inherit, never invent" and "take one task at a
time". [FEAT-214](/p/kanbanr/feature/FEAT-214) will make kanbanr enforce the boundaries with issued
scopes; until it ships, and as the statement of them after, the skill states them.

## Design

### Change
- `skill/kanbanr/SKILL.md`, in "The method by stage role", a new subsection **"Sub-agents: what each
  may do"** after "At the build role":
  - the boundary table per role: a **build** agent may read everything, record `task state` and
    `test` evidence on its own item, and commit only on its item's branch naming the item; it may not
    move, approve, sign off, define, edit specs or docs, touch other items, batch, push or sync, and
    its tests stay on temporary boards. A **design** agent is read-only;
  - the coordinator's duties: put the role's table in every brief, verbatim; have build agents record
    their own progress as tasks start and land; review an agent's branch and update its item's tasks
    at once, never waiting for its report; the board never lags the code; no agent pushes;
  - questions and out-of-scope work come back to the coordinator, never decided by the agent;
  - a pointer to FEAT-214's scopes once they exist.
  The two existing sub-agent lines (design role, build role) point to it.
- `docs/src/using/the-method.md`: the same subsection for people (FEAT-194 R-1 keeps the two
  sections side by side).
- `api/crates/kanbanr-cli/src/skill.rs`: a guard test, `skill_states_sub_agent_boundaries`, that the
  embedded skill has the subsection and its two roles.
- CHANGELOG under [Unreleased], `tools/docs/sync.sh`.

### Test plan
| Req | Test |
|---|---|
| R-1 | `skill_states_sub_agent_boundaries` (unit); `manual: the skill's and the book's sub-agent subsections agree` |

### Implementation tasks
1. The skill subsection and pointers; the book subsection; the guard test; changelog. Depends on: none.

### Affects docs
docs/src/using/the-method.md, skill/kanbanr/SKILL.md, docs/src/project/changelog.md.
