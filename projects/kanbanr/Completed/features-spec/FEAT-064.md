# A wave's lessons belong in its retrospective

## Problem
Lessons are stored as scored rows so they can be matched to future work and decay — which is right — but there is no view of "what this wave taught us". The retro document, which is where a reader looks for exactly that, does not mention them, and `Lesson.from_retro` exists as a field that nothing populates.

## Behavior
- A retrospective includes the lessons recorded against that wave's items, with the confidence they carried when it was written.
- `kanbanr lesson add --from-retro <path>` records which retrospective promoted a lesson, and those lessons appear in that document.
- A lesson that has since retired still appears in the retro of the wave that produced it, marked retired: a retrospective is a historical account, and the wave did learn it.
- Rendered, never stored twice: the rows in lessons.yaml stay canonical.

## Out of scope
Changing how lessons are stored or scored.