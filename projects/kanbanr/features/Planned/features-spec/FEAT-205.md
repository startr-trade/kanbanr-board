# Board cards say plainly what an item needs next

## Why
On 20 Oct 2026 the user found the board "totally confusing": a Planned card showed a pill
"→ In Progress ✓" and an In Progress card "→ Completed ✓". The pill (FEAT-112/FEAT-117) means "the
next stage's gate passes", but it is styled like a status chip, and its ✓ counts only the gate's
conditions — not open tasks, and not the sign-offs the stage still needs. FEAT-202 showed
"→ Completed ✓" at 1 of 2 tasks with `docs-folded` not given.

## Design

Decided by the user on 20 Oct 2026: plain words, honest.
- **Readiness** (`readiness::NextStage`, FEAT-177's typed view): gains `signoffs: Vec<String>` — the
  sign-offs the stage still needs — and `tasks_open: usize`. The public schema and `openapi.json`
  are regenerated; the contract test covers the new fields.
- **The card** (`web/src/components/bits.tsx`, `FeatureCard`), in order:
  - conditions missing → "<Stage> needs N" (tooltip lists them);
  - tasks open → no readiness pill (the tasks chip already says "1/2 tasks");
  - only sign-offs missing → "waiting for sign-off <name>[, …]";
  - nothing missing → "ready for <Stage>"; for an end stage, "ready to complete".
- **Style**: a hint, not a status chip — no arrow, muted outline (`chip hint`), distinct from the
  status columns' own labels; `check:ui` keeps every colour token defined.

### Test plan
| Req | Test | Where |
|---|---|---|
| R-1 | `readiness::tests::next_stage_names_signoffs_and_open_tasks` | core |
| R-2 | `web::card_says_what_is_next` (check script rendering `FeatureCard` text for the five cases above) | web/scripts/check-ui… |
| R-3 | `manual: the kanbanr board reads correctly in the monitor` (screenshot) | review |

### Implementation tasks
1. Core: `signoffs` and `tasks_open` on `NextStage`; schema regenerated; R-1.
2. Web: the card text and the hint style; the types; R-2.
3. CHANGELOG "Fixed", make ci, the manual check.

### Affects docs
docs/src/using/the-monitor.md (what a card shows).
