# Decisions in Claude Code: a plan to scope an item, a question to decide it

## Problem
The user wants to work without the browser for writes, and without a terminal. Today the skill
scopes a new item in conversation and then asks the user to approve with `kanbanr approve` or the
Review page's button; it forbids Claude from recording any verdict. So every approval, ratification,
sign-off and decision means leaving Claude Code. Claude Code already has the two tools a decision
needs: plan mode (a brief the user reads and accepts or sends back) and a question dialog with
explicit choices.

## Behavior
- **A new item is scoped in plan mode.** Asked for a feature, Claude enters plan mode, reads the
  charter and the code, asks only what it cannot find (a few questions at a time), and writes the
  plan as the item's brief: statement, goals, the six Zachman answers, EARS requirements with named
  tests, and the stage it starts in. Exiting plan mode with the user's acceptance creates the item
  and records the user's approval of exactly that definition; sending it back revises the plan.
- **The review queue is worked in the conversation.** "Let's review" (or a session that finds items
  waiting) walks the queue one item at a time: Claude shows the brief and asks one question whose
  answers are the verdicts that item can take — Approve / Ratify / Sign off <name> / Accept or
  Reject a decision — plus "Change it" (Claude revises the definition, which comes back to the
  queue) and "Skip". The chosen verdict is recorded at once, as the user, then the next item.
- **A verdict is recorded only from the user's explicit choice in that dialog or plan**, never
  inferred from conversation, and only for the definition the user was shown: `kanbanr approve`,
  `ratify` and `signoff` gain `--rev <content-rev>`, which refuses if the definition changed after
  it was shown. The skill passes it every time.
- The skill's approval section, the docs, and the setup interview's wording say so; the browser and
  the CLI stay available for anyone who prefers them.

## Out of scope
Moving items by drag-and-drop in the monitor (a separate decision). Approvals by anyone other than
the user at the keyboard.
