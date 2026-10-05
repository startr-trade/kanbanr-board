# Designing a process with Claude, in the setup interview and after

## Problem
The setup interview offers the built-in processes or "load your own with --from-file". Nothing helps
the user design their own gates, and nothing offers processes they already saved.

## Behavior
- Setup interview, "c. Process", and any later "let's change our process", in plan mode:
  saved processes offered first; "our own" starts from the nearest built-in; one question per stage
  ("what must be true before work enters <Stage>?") with options from `process checks --json`;
  anything kanbanr can't see becomes a named sign-off; block or warn, branch stage, end stage and
  rework moves asked together; name it and choose board or personal; the draft is checked with
  `process check` and its working agreement and diagram go in the plan. Accepting the plan accepts
  the process. A changed process offers `process update` per project, one question each.
- Docs: processes.md "Designing a process with Claude" and "Saving and sharing processes";
  with-claude.md; CHANGELOG; the stability policy entry for the process file, the board's
  `processes/` folder and the `process` commands.
- ADR-0013 "Shared processes are board data", proposed, accepted when this lands.

## Out of scope
Editing processes in the monitor.
