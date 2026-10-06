# Defect: setup's first commit fails when git has no identity, and setup carries on

## Problem
In the FEAT-171 walkthrough (design-shop), the setup plan's `git commit -m "[no-ref] initial
commit"` failed: git on the machine had no user.name or user.email. The setup went on to the next
commands instead of stopping, and Claude then retried the commit with the identity passed for that
one commit. The setup interview already asks for the commit identity (for the board), but the
initial commit in the project's repository relies on git's own configuration.

## Behavior
- The setup plan's initial commit uses the identity the interview agreed:
  `git -c user.name="<name>" -c user.email="<email>" commit …`, when git has none configured; the
  user's git configuration is never changed. The plan says so, and tells the user to set it for
  their own commits.
- The skill runs the setup commands so that the first failure stops the rest (one command at a
  time, or joined with `&&`), as the plan promises.

## Out of scope
Setting the user's git configuration for them.
