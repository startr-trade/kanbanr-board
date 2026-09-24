# Surfacing: feature show, query --goal, monitor sections

## Problem
`kanbanr feature show` is the markdown export and is Claude's whole view of an item, so anything not rendered there is invisible; the monitor likewise shows none of the new data.

## Behavior
- `export::to_markdown` gains `## Definition` and `## Requirements` sections, rendered only when a definition is present so legacy output stays byte-identical.
- `query`: `--goal G-1` filter; definition text under `--full-text` (no extra IO).
- Monitor sections (not new pages): Definition grid with gap chips and a Requirements section (EARS text, ISO badges, quality scenario, TDD test badges) on the feature page; a 'no definition' chip on non-terminal board cards; a single 'Needs attention' panel on the Board covering unapproved items, definition gaps and requirements without tests.

## Out of scope
A page per data type. A page must answer a regularly asked question no existing page answers: the Charter page (FEAT-046) qualifies; NFR/EARS/approval/lessons/ADR/retro views are sections, filters or documents; the Zachman matrix ships as `trace --zachman` output; a Traceability page is built only if `kanbanr trace` proves it is reached for.
