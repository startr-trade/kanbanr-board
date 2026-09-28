# A recorded bypass is never reconciled

## Problem

`--unapproved "<reason>"` lets work start without an agreed definition and records why. That is the
right design: a bypass that leaves a trace beats one that is silent. But the trace only lives on the
item, and every surface that lists it excludes terminal statuses — the doctor's scope gate has since
FEAT-049, and the review queue does as of FEAT-078.

So the lifecycle of a bypass is: recorded, reported while the work is in flight, and then **silently
gone** the moment the item completes. FEAT-072, FEAT-073 and FEAT-075 on this board were each built
under a recorded escape and are now listed by nothing.

Its shape is the one this project keeps finding: **silence read as absence**. A clean `doctor` is
supposed to mean "nothing needs attention", and here it means "the things that needed attention
finished before anyone looked".

Nothing is lost — `kanbanr check <CODE>` still fails the item and its page still shows the reason —
but both require knowing which item to ask about, which is exactly what a list is for.

## What needs deciding first

This is not obviously a bug with one fix, which is why it is a separate item rather than a line in
FEAT-078. What should reconciliation mean?

- **Acknowledge after the fact** — a distinct verdict ("built without prior agreement, reviewed
  since") that neither pretends the gate was honoured nor leaves the item unresolved. Honest, and it
  admits a second kind of approval into the model.
- **Approve retroactively** — one verdict, whose `rev` pins a definition that describes work already
  merged. Simple, and it makes the approval record unable to distinguish agreement from ratification,
  which is the distinction the whole gate exists to draw.
- **A standing list** — `kanbanr bypasses`, or a doctor rule exempt from the terminal gate. Changes no
  model, and risks becoming a list nobody empties.
- **Accept it** — the reason on the item is the record, and asking for more is process for its own
  sake. Defensible, and it should then be written down as a decision rather than left as a gap.

The trade-off runs through what an approval record is allowed to claim, so it wants an ADR, not a
preference.

## Out of scope

Removing or weakening `--unapproved`. The escape is what keeps the gate honest under real pressure; a
gate with no recorded bypass is one that gets bypassed with `--no-verify` instead.
