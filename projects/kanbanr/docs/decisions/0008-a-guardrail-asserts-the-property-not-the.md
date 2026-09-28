---
id: ADR-0008
status: accepted
date: 2026-09-28
deciders:
- Venkatraman B
affects:
- FEAT-081
- FEAT-076
driven_by:
- FEAT-081/R-3
- FEAT-081/R-1
quality:
- Interaction Capability
- Maintainability
zachman:
- How
layer: conceptual
---

# A guardrail asserts the property, not the shape of the fix

## Context

This board has now recorded the same mistake twice, in unrelated areas.

`FEAT-076/R-2` required that an element performing an action be styled as a button rather than as a
label. The fix changed `className="chip"` to `"btn"`; the guardrail written beside it asserted that no
action element carries the `chip` class. Both were satisfied, and the button still looked exactly like
a tag, because `.btn` and `.chip` declared the same background. The user reported the same complaint
a second time (`FEAT-081`).

`FEAT-066` had the same shape from the other direction: a `read(limit)` that returned ten rows for a
request of seven, because an early `return` skipped the truncation — the test asserted the rows came
back, not that the count was honoured.

The forces:

- **A guardrail is cheap to write from the diff in front of you.** The fix is concrete and the
  property is abstract, so the test tends to describe what just changed. `Interaction Capability` is
  the quality most exposed to this, because the property lives in what a person perceives and the fix
  lives in a class name or a token.
- **A test that mirrors the fix cannot fail on the next instance of the same bug.** It is not weak
  coverage; it is coverage aimed at the wrong thing, and it reports success while the defect stands.
  That is worse than no test, because it also stops anyone looking.
- **Some properties genuinely are not mechanically checkable.** Legibility, wording and layout are
  judgement. A rule that demanded a machine check for every user-visible requirement would be
  ignored, and `ADR-0004` already settled that a guardrail which cannot run steps aside.

## Decision

We will write each guardrail against the **property the requirement is about**, and where that
property is not directly checkable, against the **nearest mechanically checkable proxy for it** —
never against the shape of the change that satisfied it once. A requirement's test must be able to
fail on a *different* implementation of the same defect.

Concretely, for a user-visible requirement:

1. Name the property in the requirement text, in the user's terms ("recognisable as a control without
   hovering"), not in the codebase's ("does not carry the `chip` class").
2. Find the checkable proxy closest to that property. For the affordance it is the stylesheet:
   `.btn` and `.chip` must not share a background — cheap, deterministic, no browser.
3. **Verify the check by reverting the fix.** A guardrail that has never been observed to fail is an
   assumption. `check:ui` was run against the reverted surface and exited 1, naming the shared
   background; that run is the evidence, and it belongs in the requirement's record.
4. Where no proxy exists, keep the test `manual` and say what a person must look at. An honest manual
   test beats an automated one that checks the wrong thing.

## Alternatives considered

- **Screenshot or computed-style diffing.** It would have caught this directly, and the Selenium flow
  already exists. Rejected as the default: it needs Docker, it is slow, and its failures are noisy
  enough that a suite like that stops being run — at which point it protects nothing. Kept available
  for properties with no cheaper proxy.
- **Review discipline instead of a check.** Rejected by `L-21`: a greppable rule belongs in a script,
  because the reintroduction looks perfectly ordinary in a diff.
- **Require every requirement to carry an automated test.** Rejected. It forces an automated test
  where none is honest, and the predictable result is a test written from the fix — the exact failure
  this decision exists to prevent.

## Consequences

**Positive.** A guardrail that can fail on a variant of the same bug. The deliberate revert also
documents, for free, what the check is actually sensitive to. Requirement text written in the user's
terms survives refactoring, because it does not name any implementation.

**Negative.** Finding the property costs more thought than mirroring the fix, and the revert is an
extra step on every guardrail. Some proxies are loose — a shared background is not the same claim as
"visibly a control", and a sufficiently odd pair of distinct backgrounds would still pass. That is
accepted: the proxy narrows the failure mode that actually occurred, rather than pretending to close
the whole space.

**Trade-off.** We buy Interaction Capability and Maintainability with Maintainability's own cost —
more work per guardrail, and one more step to skip under pressure.

## Compliance

- `web/scripts/check-affordance.mjs` asserts `.btn` and `.chip` do not share a background, alongside
  the class rules. Reverting `--control` to `--panel-2` makes it exit 1.
- `FEAT-081/R-3`'s quality scenario names that revert run as its measure, so the ADR's central claim
  carries its own evidence.
- `kanbanr doctor` already reports a measure that names no test as an unsupported claim, which is the
  mechanism that surfaces a guardrail with nothing behind it.
