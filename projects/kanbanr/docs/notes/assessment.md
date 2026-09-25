---
refs:
- G-1
- G-2
- G-3
- G-4
- G-5
---

# Honest assessment — September 2026

*Rewritten after MS-006. The previous version described a tool with no charter, no requirements, no
evidence and no traceability; its history is in this document's git log. Everything below is
measured from the board or counted from the source, and where a number is flattering for the wrong
reason, that is said.*

## Where it stands

26,000 lines of Rust, 2,200 of TypeScript, 154 tests. 63 work items, 57 complete. Six architecture
decisions, eight lessons, 48 of 49 requirements proven by a green test. `kanbanr doctor` reports
clean.

The thing it set out to be — a durable, external system of record for an AI agent doing real work —
exists and is used daily by its author. A session that ends mid-feature resumes from `kanbanr board`
with no human recap. That was goal **G-1**, and it is met.

## What it is betting on

That the **behavioural contract is the product**, not the storage. Anything can hold a list of
tasks. What kanbanr does that a task list does not is oblige the agent working on the project to
record why an item exists, get that reasoning agreed before building, prove each requirement with a
test the tool watched pass, and leave a path from any line of code back to the goal it serves.

The second bet is **derive, never store**. Cycle time comes from transition history, not a field
anyone fills in. Whether a defect escaped is computed from whether the work it came from was
already done. The traceability view is rebuilt on every call. Nothing self-reports, so nothing can
flatter itself — and anything that cannot be derived is reported as absent rather than estimated.

## What is genuinely good

**The method finds real problems.** Four defects this milestone were found by pointing a new tool at
the project's own board minutes after merging it: a retrospective that called twelve planned items
"scope growth", an auto-completion path that silently recorded no transition (so cycle time
described only hand-moved items), a warning that fired on all 27 requirements, and a guardrail that
matched the commit message explaining it. Every one passed its unit tests.

**Evidence is measured, not claimed.** A PostToolUse hook reads real test output and flips the
tracked tests; a green recorded at an older revision is reported as stale rather than counted;
`kanbanr tests --write` un-proves a requirement whose test no longer exists. There is no path by
which an agent marks its own work proven.

**The guardrails degrade rather than block** (ADR-0004). The git hooks exit silently without the CLI
on PATH, `doctor` never fails a write, and only two things are refused — a reference to something
the board does not have, and a commit naming nothing at all. Both are fixable in the message the
author is already writing.

**Nine schema additions, zero migrations.** Every new field is optional and skipped when empty, so a
board written months ago re-serializes byte for byte (ADR-0005). The check is manual and has run on
every item of this milestone.

## What is honestly wrong

**The escape rate is 100%.** All four defects were found *after* the work was called done. The tool's
own metric is condemning its own process, and it is right to: the gates verify that code compiles,
lints and passes tests — not that the feature is fit for the board it will run against. The fix is
not more tests. It is running each new read against real data before merging, which is now lesson
L-1 and was learned the expensive way four times.

**Nine definitions are approved by nobody.** The approval gate is the feature this entire milestone
was built around — the answer to seven hours of subagent work rejected for reasoning that was never
written down. Every item since has been started with `--unapproved "auto-pilot"`. The mechanism
worked exactly as designed: the escape is recorded, visible on the board, and reported by `doctor`.
The *practice* did not happen. A gate that is always escaped is a gate in name only, and this is the
most important thing on this page.

**The method may still be too heavy for one person.** An item carries a statement, a goal link, six
Zachman dimensions, and typically five to nine EARS requirements each with tests — for a
single-developer tool. The author asked whether this was too complicated and was told "yes, in
parts"; it was adopted at full depth anyway. It has paid for itself in caught defects so far. It has
not yet been paid for by anyone who did not design it.

**Evidence decays the moment anything is committed.** 45 of 49 requirements currently carry greens
from an earlier revision, because every commit moves HEAD. The display was fixed so the warning does
not fire on everything (FEAT-062), but the underlying truth is unchanged: evidence is only as
current as the last full test run, and nothing forces one.

**Flow numbers are thin.** Cycle time reads p50 2 minutes — true, and useless: only items moved by
hand during the last two sessions carry history, and they were completed in the same sitting. Items
that finished before FEAT-061 have no transitions at all. The number will mean something in about a
month of ordinary use, and not before.

**Nobody outside has used it.** Every judgement here is the author's, about their own tool, measured
by instruments the author wrote. The contribution bar is documented and has never been met by a
contributor. Until it is, "a contributor can meet this bar" is a hypothesis.

## How it compares

Against a `TODO.md`: not comparable — this survives sessions, holds reasoning, and enforces a
contract. Against **Task Master AI** and similar MCP task tools: they have broader agent reach (see
ADR-0006, which commits to an MCP surface but has not built it) and no equivalent of the approval
gate or evidence capture. Against **Linear / Jira / GitHub Projects**: they win on collaboration,
integrations and polish, and are not trying to solve this problem — none of them asks an agent to
prove a requirement before calling it done. Against **ADR tooling** (adr-tools, log4brains): those do
decisions well and nothing else; here decisions are one node in a graph that reaches code.

The honest niche is narrow and real: **one developer, one machine, an AI agent doing most of the
typing, and a need to justify later what was built and why.**

## What to do better, in order

1. **Use the gate.** Review and approve (or reject) the nine pending definitions. If reviewing nine
   is too much work, that is itself the finding, and the bar should drop rather than be bypassed.
2. **Run every new read against the real board before merging it.** Four for four says a fixture
   proves nothing about a report.
3. **Decide whether full depth is right for every kind of item.** A chore with six dimensions and
   four EARS requirements may be honest and still not be worth it.
4. **Get one outsider through the bar.** Until then the contribution story is untested.
5. **Leave the flow numbers alone for a month**, then look. They are not evidence yet.

## Verdict

It does what it claims, and it caught its own mistakes four times in one milestone — which is the
strongest thing that can be said about a tool whose job is to keep its owner honest. The gap is not
in the machinery; it is that the one practice the machinery exists to enforce has been escaped every
time so far, by the person it was built for, with a recorded reason. The next honest step is not a
feature.
