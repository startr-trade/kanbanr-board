# Lessons learned with confidence decay

## Problem
Lessons are learned mid-execution and lost, because the only place they exist is a transcript.

## Behavior
- `projects/<id>/lessons.yaml`: `{id: L-1, at, lesson, kind, from_item, from_retro, evidence, tags, confidence, last_affirmed, status}`.
- Captured in flight (`kanbanr lesson add ... --from FEAT-043`), promoted from retro findings, offered when a defect records a root cause.
- Confidence decays unless reaffirmed; `affirm|contradict` with contradiction weighted heavier; below threshold a lesson retires — kept, not deleted.
- Surfacing: the SessionStart hook prints the few highest-confidence active lessons; `kanbanr lessons --for <CODE>` matches an item's labels/kind/goals so they are read BEFORE work starts; the Charter tab lists them beside the goals.
- Dedupe by normalized-text key.

## Out of scope
Cross-project or cross-agent sharing.
