# Sign-offs: withdraw, and offer only the next stage's

Two problems were found in use.

1. **No way to withdraw.** A sign-off given by mistake cannot be withdrawn. Approvals have `unapprove --reason`; sign-offs have no equivalent.
2. **Offered too early.** When a workflow lets an item skip stages (for example Implementation → Operations), the review page offers the later stage's sign-off while the item is still being built. A person can then record `release` before there is anything to release.

Scope:
- `kanbanr signoff <CODE> <NAME> --withdraw --reason "…"`. The withdrawal is recorded as an event; the earlier sign-off is kept as history and stops counting.
- A Withdraw button in the monitor next to a recorded sign-off.
- The review queue offers a sign-off only for the immediate next stage in workflow order, not for every stage reachable in one transition.
