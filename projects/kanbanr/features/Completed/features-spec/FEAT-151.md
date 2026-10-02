# An older kanbanr keeps fields it does not know when it rewrites a board file

## Problem
Writing the stability policy (FEAT-148) showed a gap in the promise it makes. An older kanbanr
reads a board file with fields it does not know and ignores them; but when it then rewrites that
file (a move, a task state, an edit) those fields are gone. The item, milestone and config models
keep no unknown keys. So after 1.1 adds a field,
a 1.0 binary on another machine sharing the board silently deletes it. The policy currently says
"upgrade together"; the protection has to ship in 1.0 itself to cover 1.0 → 1.x mixing.

## Behavior
- Feature items, milestones, the project config and the charter keep every key they do not know,
  and write it back unchanged, in the same place in the file where practical.
- A test writes a file with an unknown field (top-level and nested in a requirement), rewrites it
  through a move, a task change and an edit, and finds the field intact.
- The stability chapter drops the "upgrade together" caveat for fields (it stays true for a newer
  `schema_version`, which an older binary refuses anyway).

## Out of scope
Keeping comments or formatting a person added by hand to the YAML.
