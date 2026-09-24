# Surfacing: feature show, query --goal, monitor sections

## Problem
`kanbanr feature show` is the markdown export and is Claude's whole view of an item, so anything not rendered there is invisible; the monitor likewise shows none of the new data.

## Behavior
- `export::to_markdown` gains `## Definition` and `## Requirements` sections, rendered only when a definition is present so legacy output stays byte-identical.
- `query`: `--goal G-1` filter; definition text under `--full-text` (no extra IO).
- Monitor: Definition grid with gap chips, Requirements section with ISO badges, scenario and TDD badges; a 'no definition' chip on non-terminal board cards. Reuse existing CSS classes.

## Out of scope
A Doctor page in the monitor — gaps show in place.
