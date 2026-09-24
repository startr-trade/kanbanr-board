# Surfacing and search

## Problem
`kanbanr feature show` is the markdown export and is Claude's whole view of an item, so anything not rendered there is invisible. Troubleshooting is worse: `query --full-text` searches only item titles and specs, while the graph now also holds requirements, tests, docs, ADRs, lessons and retros — and a hit without its context does not help.

## Behavior
- `export::to_markdown` gains `## Definition` and `## Requirements` sections, rendered only when a definition is present so legacy output stays byte-identical.
- **Text search across the graph**: items, requirements, tests, docs, ADRs, lessons and retros; every hit renders the path up to its goal ("'mirror' found in FEAT-043/R-2 -> G-2"), because where alone is not useful.
- **Structured troubleshooting filters on the same command**: `--goal`, `--quality`, `--violates`, `--adr`, `--since`, and `--gap why|test|approval` (requirements with no green test or a stale `checked_rev`, items serving no goal, goals with no items, scope added after approval, defects introduced_by an item including fix-induced chains). `--json` throughout so it composes.
- Monitor sections (not new pages): Definition grid with gap chips and a Requirements section (EARS, ISO badges, quality scenario, TDD badges) on the feature page; a 'no definition' chip on non-terminal board cards; a 'Needs attention' panel on the Board; and ONE global search box rather than more tabs.

## Out of scope
A search index — the board is ~580 KB, so brute-force scanning is instant and `load_meta` already avoids reading spec bodies unless asked. A page per data type: the Charter page (FEAT-046) qualifies; NFR/EARS/approval/lessons/ADR/retro views are sections, filters or documents; the Zachman matrix ships as `trace --zachman` output; a Traceability page is built only if `kanbanr trace` proves it is reached for.
