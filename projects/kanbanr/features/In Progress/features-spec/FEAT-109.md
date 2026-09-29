## Problem

An item started with a recorded `--unapproved` reason and then finished (FEAT-102) is reported only by `kanbanr doctor`, and agreeing to it after the fact is only `kanbanr ratify`. The Review page lists live work alone, and offers only Approve — so the one agreement the method most needs a human to give, to work already built without it, is the one the monitor cannot show or take. The user asked to do it without the CLI.

## Behavior

- The review endpoint also returns items **finished without agreement** — a recorded bypass whose definition is neither currently approved nor ratified (doctor's `unreconciled_bypass`, so the two surfaces give one answer) — marked `approval: unratified`, whatever their status.
- The Review page lists them in their own group above the rest, each with its bypass reason and a **Ratify** button that posts to the existing `…/ratify` route as the board's commit identity, exactly as Approve does. A read-only monitor shows the `kanbanr ratify <CODE>` command instead.

## Out of scope

- Ratifying items that were never started under a bypass (they are approved, not ratified).