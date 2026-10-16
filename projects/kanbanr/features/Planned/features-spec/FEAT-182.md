# Sign-offs: withdraw, and offer only the next stage's

Two problems were found in use.

1. **No way to withdraw.** A sign-off given by mistake cannot be withdrawn. Approvals have `unapprove --reason`; sign-offs have no equivalent.
2. **Offered too early.** When a workflow lets an item skip stages (for example Implementation → Operations), the review page offers the later stage's sign-off while the item is still being built. A person can then record `release` before there is anything to release.

Scope:
- `kanbanr signoff <CODE> <NAME> --withdraw --reason "…"`. The withdrawal is recorded as an event; the earlier sign-off is kept as history and stops counting.
- A Withdraw button in the monitor next to a recorded sign-off.
- The review queue offers a sign-off only for the immediate next stage in workflow order, not for every stage reachable in one transition.

## Found in use (2026-10-16): offered before it means anything
A sign-off is offered as soon as its stage is next, even when the stage's other conditions are far from met. One example is `docs-folded` before Migration, offered the moment an item enters Implementation, before any code or documentation exists. A person reviewing the queue then signs what is in front of them, and the sign-off records agreement to work that has not happened yet.

Proposal for this item: offer a sign-off in the review queue only once the gate's `requires` are met (for example, tests green), and let a sign-off name the todo task it depends on so it is offered after that task is completed. This needs a new requirement and a re-approval of the definition.
