## Problem

Found while checking the Scrum board in a browser (FEAT-123): cards for items with no definition showed `→ Ready ✓`. The readiness engine returned early for an item with no definition, reporting only a `definition` gap — and only when the check list named `definition`. The scrum preset's Ready gate asks for statement, goals, requirements, EARS and an estimate but not `definition` itself, so an undefined item passed it: the Definition of Ready was not enforced for items that had said nothing at all.

## Behavior

Any check list that reads the definition reports its absence, once, as the missing definition — whether or not it names `definition`. Checks that do not read the definition (estimated, small, in_sprint, in_release, sign-offs) are unaffected.

## Out of scope

- Other checks.