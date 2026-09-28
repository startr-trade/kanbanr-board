# Defect: the review queue asks for agreement on work that is already finished

## Problem

`kanbanr doctor` and the review queue answer the same question — what still needs someone's
agreement — and give different answers. On this board the doctor names **2** items; the queue offers
**6**.

The four extra are:

- `FEAT-072`, `FEAT-073`, `FEAT-075` — **Completed**. Approving these would record agreement, pinned
  to a definition hash, for work that is already built and merged. It cannot change anything.
- `FEAT-074` — **Deferred**, deliberately, with ADR-0007 recording why. Nothing is going to start.

The doctor already has the right rule and has had it since FEAT-049: its scope gate skips a terminal
status, then a status outside `displayed_states`. The queue has no status filter at all — it lists
every defined item whose approval is missing or lapsed.

This matters more than a count. The approval gate's premise is that agreeing must be **cheap** (G-5),
because an expensive gate gets rubber-stamped and then the gate is theatre with extra steps. A queue
that asks for four retroactive signatures alongside two real decisions is training the reviewer to
click without reading — and the items it asks about are precisely the ones where a signature means
nothing, so the training is toward exactly the wrong habit.

Found while verifying the fix for FEAT-077, by looking at what the queue actually returned.

## Behavior

- The queue asks only about items where agreement can still change what happens: it applies the same
  scope gate the doctor uses — not terminal, not a no-op disposition.
- What remains is ordered so work already in flight comes first, because an item being built without
  agreement is more urgent than one that has not started.
- The gate lives in one place, so the doctor and the queue cannot drift apart again.

## Out of scope

Reconciling work that was *finished* under a recorded bypass. `kanbanr check <CODE>` still fails such
an item and its own `started_unapproved` reason still stands on its page, so nothing is erased — but
narrowing the queue makes a pre-existing gap plainer, and it is worth stating rather than glossing:

The doctor's scope gate already excluded terminal items before this change, so once work started
under `--unapproved` reaches Completed, **no surface lists it any longer**. FEAT-072, FEAT-073 and
FEAT-075 on this board are in exactly that position. The escape hatch is honestly recorded and then
silently ages out, which means a bypass is never reconciled — the same "silence read as absence"
shape this project keeps finding. Closing it needs a decision about what reconciliation should mean
(acknowledge after the fact? approve retroactively? a standing list?), so it is `FEAT-080`, not a
line smuggled in here.
