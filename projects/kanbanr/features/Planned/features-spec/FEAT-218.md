# make ci's board check trips on an agent's scoped progress writes

## Why
The v0.3.0 release gate (22 Oct 2026) passed 69 of 70 checks; the 70th, "the real board did not
move during the run", failed on 8 board commits made meanwhile by the FEAT-217 build agent: task
states and test results on its own item, each carrying `Agent-Scope: SC-004 (build, by the agent
for FEAT-217)`. The check exists to catch a test reaching the real board. FEAT-198 already lets a
person's verdicts through; an agent's writes under a scope are the same kind of deliberate,
attributed record, and the board now expects them to happen while work runs (FEAT-214).

## Proposal (to be designed)
Count a board commit made during the run as allowed when it carries an `Agent-Scope:` trailer whose
scope was active for the item it touches, and it changes only that item's file, its activity and
events, and the board index — as verdict commits are judged today. Anything else still fails the
check.
