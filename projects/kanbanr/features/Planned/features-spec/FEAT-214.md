# Agent scopes: what a sub-agent may do, enforced by kanbanr

## Why
On 21 Oct 2026 the work was split across sub-agents (design agents, build agents in git worktrees).
Their limits lived only in each brief, as prose. Two failures followed from that:
- the briefs said "never write to the board", to keep tests away from the real board; so a build
  agent could not record its own progress, and FEAT-212's tasks read "Not started" while six of its
  commits were in;
- relaxing that by prose (agents may now record task states and tests on their own item) is still
  only as good as the agent's discipline.

The user (21 Oct 2026): "never write to the board is not the answer. We need boundaries defined for
the sub-agents precisely so that they do what is supposed to be allowed for them to do."

## The boundaries (as agreed for a build agent)
| Area | Allowed | Refused |
|---|---|---|
| Read the board | everything | — |
| Its item's record | `task state` on its item's todo-lists; `test` evidence on its item's requirements | moves, approvals, sign-offs, definitions, specs, other items, batch, docs |
| Code | commits on its item's branch only, each naming the item | commits on main, `sprint/*`, `release/*`, or any other item's branch |
| Remote | nothing | `git push`, `kanbanr sync`, pushing anything else |
| Tests | temporary boards only (the test fence) | a test reaching a real board |

A design agent's scope is read-only: every board write and every commit is refused.

## What it adds (to be designed)
- **A scope, issued per agent**: the item, the allowed operations, the branch, an expiry; recorded on
  the board (visible, auditable) and written into the agent's worktree where kanbanr reads it.
- **Enforced in three places**: the core write path (a write outside the scope is refused, naming
  the boundary it crossed); the commit guard and git hooks (commits outside the branch refused);
  pushing refused.
- **Attribution**: writes made under a scope are recorded as the person, by the agent for the item.
- **Roles**: `design` (read-only) and `build` (the table above); the skill tells Claude to issue the
  right scope before starting a sub-agent, and to brief the agent with it.
- **Drift**: a build scope expects its item's tasks to move; commits on the branch newer than the
  item's last task change are reported by name (Stop hook, `git doctor`, session start).

## Design
_To be written and agreed before build._
