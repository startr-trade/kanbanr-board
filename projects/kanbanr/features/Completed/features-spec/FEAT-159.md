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
- **The workflow drives the conversation; the skill names no workflow.** What Claude asks at each
  step is read from the project's configuration, through `kanbanr check <CODE> --json`: for each
  stage the item can move to, its `purpose`, the checks still failing, the warnings and the
  sign-offs needed. The skill maps each kind of check to one action, the same for every workflow:
  - `statement`, `goals`, `zachman` (its named columns), `requirements`, `ears`, `quality`,
    `tests_named`: drafted into the plan, asking the user only what Claude cannot work out;
  - `approved`: the user's acceptance of that plan (or an Approve question when nothing is drafted);
  - a needed sign-off: a "Sign off <name>" question; `bypass`: a Ratify question;
  - `estimated`, `in_sprint`, `in_release`: a question with the choices the board offers;
  - `tests_green`: evidence, never a question — Claude reports what is not yet green;
  - warnings: shown in the plan, with "fix it" or "go ahead and keep the warning" as the choice;
  - several possible next stages: a question asking which.
  So a preset edited, or an organisation's own process file, changes what is asked with no change
  to the skill, and the plan's heading is the stage's own `purpose`.
- The skill's approval section and the setup interview's wording say so; the browser and the CLI
  stay available for anyone who prefers them.
- **The book teaches it.** A new chapter, *Working with Claude* (first under "Using kanbanr"), shows
  the conversation as a user meets it: asking for a new item and accepting its plan; working the
  review queue by answering questions; asking for moves in plain words, or with `!` for a command;
  what each kind of missing check turns into (the same table the skill follows); and a worked item
  taken through the TOGAF preset stage by stage, with the real gate output. *Everyday use*, *The
  method* and *Processes* point to it, and the README's quick start mentions it. CI checks that the
  chapter's table names every check in the gate vocabulary, so a new check cannot ship with no
  behaviour described for it.

## Out of scope
Moving items by drag-and-drop in the monitor (a separate decision). Approvals by anyone other than
the user at the keyboard.
